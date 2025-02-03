import logging
import openai
import os
import re
import requests

from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode

from app.core.config import settings
from app.models.tenants import Tenant
from app.services.database_service import DatabaseService
from app.services.log_manager_service import save_message_log
from app.services.openai_service import generate_openai_response
from app.services.order_service import create_order
from app.services.session_manager_service import (
    close_session,
    get_or_create_session,
)

# 🔥 Configuración del Logger
logger = logging.getLogger("whatsapp_service")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

# Configurar la API de OpenAI
openai.api_key = settings.OPENAI_API_KEY


async def process_whatsapp_message(
    from_number: str, message_body, tenant_id: int, db: AsyncSession
):
    """
    Procesa un mensaje de WhatsApp (texto o audio) y maneja la lógica de respuesta.
    """
    from app.routes.whatsapp import send_whatsapp_message

    try:
        if isinstance(message_body, dict) and message_body.get("type") == "audio":
            media_id = message_body["media_id"]

            # Obtener URL del audio
            audio_url = await get_audio_url(media_id, tenant_id, db)
            if not audio_url:
                await send_whatsapp_message(
                    from_number, "No se pudo obtener el audio.", tenant_id, db
                )
                return

            # Transcribir el audio
            transcribed_text = await transcribe_audio(audio_url, tenant_id, db)
            if not transcribed_text:
                await send_whatsapp_message(
                    from_number, "No se pudo transcribir el audio.", tenant_id, db
                )
                return

            # Usamos la transcripción como el mensaje del usuario
            message_body = transcribed_text

        else:
            message_body = message_body.strip()

        # Buscar o crear sesión
        session = await get_or_create_session(from_number, tenant_id, db)

        # Obtener respuesta de OpenAI
        bot_response = await generate_openai_response(
            session.id, message_body, tenant_id, db
        )

        # Verificar si el mensaje es una orden
        if "Resumen del Pedido:" in bot_response:
            parsed_order = parse_order_details(bot_response)

            if parsed_order:
                # Guardar el pedido en la base de datos
                # (no iniciar nueva transacción si ya hay una activa)
                if not db.in_transaction():
                    async with db.begin():
                        order, order_number = await create_order(
                            from_number, parsed_order, tenant_id, db
                        )

                else:
                    order, order_number = await create_order(
                        from_number, parsed_order, tenant_id, db
                    )

                if order:
                    # 🔍 **Reemplazar el total en bot_response**
                    bot_response = re.sub(
                        r"Total: \d+(\.\d+)? EUR",
                        f"Total: {order.total:.2f} EUR",
                        bot_response,
                    )

                    base_url = f"{settings.BASE_URL}/payments/payment-form"
                    query_string = urlencode(
                        {
                            "order_id": order_number,
                            "amount": order.total,
                            "tenant_id": tenant_id
                        }
                    )
                    payment_url = f"{base_url}?{query_string}"

                    confirmation_msg = (
                        f"✅ Tu pedido ha sido registrado con éxito.\n\n"
                        f"Pedido N° {order_number}\n\n"
                        f"📌 Si necesitas hacer cambios, avísame antes de realizar el pago.\n\n"
                        f"🚀 En cuanto se registre el pago, nos pondremos manos a la obra.\n\n"
                        f"🔗 Puedes realizar el pago aquí:\n {payment_url}"
                    )

                    await send_whatsapp_message(
                        from_number, confirmation_msg, tenant_id, db
                    )

                else:
                    await send_whatsapp_message(
                        from_number, "❌ Error al registrar el pedido.", tenant_id, db
                    )

        # Guardar en el historial de conversación
        await save_message_log(session.id, message_body, bot_response, tenant_id, db)

        # Enviar respuesta al usuario
        await send_whatsapp_message(from_number, bot_response, tenant_id, db)

    except Exception as e:
        logger.error(f"❌ Error procesando mensaje de WhatsApp: {e}", exc_info=True)


async def send_message(to: str, body: str, tenant_id: int, db: AsyncSession):
    """
    Envía un mensaje de WhatsApp utilizando la API de Meta.
    """
    try:
        logger.info(f"📩 Enviando mensaje a {to} desde tenant_id {tenant_id}...")

        # 🔍 Obtener el token de WhatsApp del tenant
        result = await db.execute(
            select(Tenant.whatsapp_token).where(Tenant.id == tenant_id)
        )
        whatsapp_token = result.scalar_one_or_none()

        if not whatsapp_token:
            logger.error(
                f"❌ No se encontró el token de WhatsApp para tenant_id {tenant_id}"
            )
            raise HTTPException(
                status_code=400,
                detail="No se encontró el token de WhatsApp para este tenant.",
            )

        url = settings.WHATSAPP_API_URL
        headers = {
            "Authorization": f"Bearer {whatsapp_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }

        logger.debug(f"🔍 Payload enviado: {payload}")
        logger.debug(f"🔍 Headers enviados: {headers}")

        response = requests.post(url, json=payload, headers=headers)

        logger.debug(
            f"🔍 Respuesta de WhatsApp API: {response.status_code} - {response.text}"
        )

        if response.status_code != 200:
            logger.error(f"❌ Error enviando mensaje: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error enviando mensaje: {response.text}",
            )

        logger.info(f"✅ Mensaje enviado correctamente a {to}")

    except Exception as e:
        logger.error(f"❌ Error en send_message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error enviando mensaje: {str(e)}")


def parse_order_details(order_text: str) -> dict:
    """
    Extrae los datos de un resumen de pedido y los convierte a JSON,
    asegurando que los extras y exclusiones se asignen correctamente al plato
    correspondiente.
    Además, recalcula dinámicamente el total para evitar errores.
    """
    try:
        # Expresiones regulares para capturar los datos clave
        mesa_match = re.search(r"Mesa:\s*(\d+)", order_text)

        # Patrón para platos y bebidas
        item_pattern = re.compile(
            r"-\s*(Plato|Bebida)\s*\d+:\s*([\w\sÁÉÍÓÚáéíóúüÜñÑ]+)\s*-\s*([\d.]+)€\sx(\d+)"
        )

        # Patrón para extras
        extra_pattern = re.compile(
            r"--> Extra:\s*([\w\sÁÉÍÓÚáéíóúüÜñÑ]+)\s*-\s*([\d.]+)€\sx(\d+)"
        )

        # Patrón para ingredientes excluidos ("Sin:")
        sin_pattern = re.compile(r"--> Sin:\s*([\w\sÁÉÍÓÚáéíóúüÜñÑ]+)")

        # Construcción de la estructura JSON
        order_data = {
            "mesa": int(mesa_match.group(1)) if mesa_match else None,
            "pedido": [],
            "total": Decimal("0.00"),  # Se inicializa en 0.00
        }

        last_plato = None  # Referencia para asociar extras a platos

        # Dividir el pedido en líneas y analizarlas
        for line in order_text.split("\n"):
            item_match = item_pattern.search(line)
            extra_match = extra_pattern.search(line)
            sin_match = sin_pattern.search(line)

            # Si encontramos un plato o bebida
            if item_match:
                tipo, nombre, precio, cantidad = item_match.groups()
                precio = Decimal(precio)
                cantidad = int(cantidad)
                subtotal = precio * cantidad

                item_data = {
                    "tipo": tipo,
                    "nombre": nombre.strip(),
                    "precio": precio,
                    "cantidad": cantidad,
                    "subtotal": subtotal,
                    "extras": [],
                    "sin": [],
                }

                order_data["pedido"].append(item_data)
                order_data["total"] += subtotal  # **SUMA AL TOTAL GENERAL**

                # Guardamos referencia del último plato para extras
                if tipo == "Plato":
                    last_plato = item_data
                else:
                    last_plato = None  # Si es bebida, no se le añaden extras

            # Si encontramos un extra, lo asignamos al último plato detectado
            elif extra_match and last_plato is not None:
                nombre_extra, precio_extra, cantidad_extra = extra_match.groups()
                precio_extra = Decimal(precio_extra)
                cantidad_extra = int(cantidad_extra)
                subtotal_extra = precio_extra * cantidad_extra

                extra_data = {
                    "nombre": nombre_extra.strip(),
                    "precio": precio_extra,
                    "cantidad": cantidad_extra,
                    "subtotal": subtotal_extra,
                }

                last_plato["extras"].append(extra_data)
                order_data["total"] += subtotal_extra  # **SUMA AL TOTAL GENERAL**

            # Si encontramos un "Sin:", lo asignamos al último plato detectado
            elif sin_match and last_plato is not None:
                nombre_sin = sin_match.group(1).strip()
                last_plato["sin"].append(nombre_sin)

        order_data["total"] = round(order_data["total"], 2)

        logger.info(f"✅ Pedido parseado: {order_data}")
        return order_data

    except Exception as e:
        logger.error(f"❌ Error al parsear el pedido: {e}", exc_info=True)
        return {}  # Retorna un JSON vacío si hay un error


async def get_audio_url(media_id: str, tenant_id: int, db: AsyncSession) -> str:
    """
    Obtiene la URL de descarga del archivo de audio desde WhatsApp API.
    """
    try:
        result = await db.execute(
            select(Tenant.whatsapp_token).where(Tenant.id == tenant_id)
        )
        whatsapp_token = result.scalar_one_or_none()
        
        
        url = f"https://graph.facebook.com/{settings.WHATSAPP_VERSION_API}/{media_id}"
        headers = {"Authorization": f"Bearer {whatsapp_token}"}

        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response.status_code != 200:
            logger.error(f"❌ Error obteniendo URL del audio: {response_data}")
            return None

        audio_url = response_data.get("url")

        return audio_url

    except Exception as e:
        logger.error(f"❌ Excepción en get_audio_url: {e}", exc_info=True)
        return None


async def transcribe_audio(audio_url: str, tenant_id: int, db: AsyncSession) -> str:
    """
    Transcribe un archivo de audio a texto utilizando OpenAI Whisper.
    """
    try:
        result = await db.execute(
            select(Tenant.whatsapp_token).where(Tenant.id == tenant_id)
        )
        whatsapp_token = result.scalar_one_or_none()
        
        # Descargar el archivo de audio con autenticación
        headers = {"Authorization": f"Bearer {whatsapp_token}"}
        response = requests.get(audio_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"❌ Error al descargar el audio: {response.status_code}")
            return None

        audio_path = "temp_audio.ogg"
        with open(audio_path, "wb") as f:
            f.write(response.content)

        # Enviar a OpenAI Whisper
        with open(audio_path, "rb") as f:
            transcription = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )

        # Acceder correctamente al texto transcrito
        transcribed_text = transcription.text.strip()

        # Eliminar archivo temporal
        os.remove(audio_path)

        return transcribed_text

    except Exception as e:
        logger.error(f"❌ Error transcribiendo el audio: {e}", exc_info=True)
        return None
