import re
import requests

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.context_manager_service import update_context
from app.services.log_manager_service import save_message_log
from app.services.openai_service import generate_openai_response
from app.services.session_manager_service import close_session, get_or_create_session


async def process_whatsapp_message(
    from_number: str, message_body: str, db: AsyncSession
):
    """
    Procesa un mensaje de WhatsApp.
    """
    # Importación diferida para evitar dependencias circulares
    from app.routes.whatsapp import send_whatsapp_message

    # Busca o crea una sesión activa para el usuario
    session = await get_or_create_session(from_number, db)

    # Genera una respuesta de OpenAI en base al mensaje del usuario
    bot_response = await generate_openai_response(session.id, message_body, db)
    
    # Detectar si el mensaje es un resumen de pedido:
    if "Resumen del Pedido:" in bot_response:
        parsed_order = parse_order_details(bot_response)
        print("Pedido parseado: !!!!", parsed_order)
        
        # Guardar el pedido en el contexto de la sesion
        await update_context(session.id, {"current_order": parsed_order}, db)

    # Guarda el log de la conversación
    await save_message_log(session.id, message_body, bot_response, db)

    # Envía la respuesta al usuario
    await send_whatsapp_message(from_number, bot_response)

    # Simular cierre de sesión (ejemplo: usuario envía "finalizar")
    if message_body.lower() == "finalizar":
        await close_session(from_number, db)


async def send_message(to: str, body: str):
    url = settings.WHATSAPP_API_URL
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error enviando mensaje: {response.text}",
        )

def parse_order_details(order_text: str) -> dict:
    """
    Extrae los datos de un resumen de pedido y los convierte a JSON,
    asegurando que los extras y las exclusiones se asignen correctamente al plato correspondiente.
    """
    try:
        # Expresiones regulares para capturar los datos clave
        mesa_match = re.search(r"Mesa:\s*(\d+)", order_text)
        total_match = re.search(r"Total:\s*([\d.]+)\s*EUR", order_text)
        
        # Patrón para platos y bebidas
        item_pattern = re.compile(r"-\s*(Plato|Bebida)\s*\d+:\s*([\w\sÁÉÍÓÚáéíóúüÜñÑ]+)\s*-\s*([\d.]+)€\sx(\d+)")

        # Patrón para extras
        extra_pattern = re.compile(r"--> Extra:\s*([\w\sÁÉÍÓÚáéíóúüÜñÑ]+)\s*-\s*([\d.]+)€\sx(\d+)")

        # Patrón para ingredientes excluidos ("Sin:")
        sin_pattern = re.compile(r"--> Sin:\s*([\w\sÁÉÍÓÚáéíóúüÜñÑ]+)")

        # Construir estructura JSON
        order_data = {
            "mesa": int(mesa_match.group(1)) if mesa_match else None,
            "pedido": [],
            "total": float(total_match.group(1)) if total_match else None,
        }

        last_plato = None  # Variable para rastrear el último plato agregado

        # Dividir el pedido en líneas y analizarlas
        for line in order_text.split("\n"):
            item_match = item_pattern.search(line)
            extra_match = extra_pattern.search(line)
            sin_match = sin_pattern.search(line)

            # Si encontramos un plato o bebida
            if item_match:
                tipo, nombre, precio, cantidad = item_match.groups()
                item_data = {
                    "tipo": tipo,
                    "nombre": nombre.strip(),
                    "precio": float(precio),
                    "cantidad": int(cantidad),
                    "extras": [],
                    "sin": []  # Lista para ingredientes excluidos
                }
                order_data["pedido"].append(item_data)

                # Si es un plato, guardamos referencia para asociarle extras o ingredientes excluidos
                if tipo == "Plato":
                    last_plato = item_data
                else:
                    last_plato = None  # Si es una bebida, los extras y exclusiones no aplican

            # Si encontramos un extra, lo asignamos al último plato detectado
            elif extra_match and last_plato is not None:
                nombre_extra, precio_extra, cantidad_extra = extra_match.groups()
                last_plato["extras"].append({
                    "nombre": nombre_extra.strip(),
                    "precio": float(precio_extra),
                    "cantidad": int(cantidad_extra),
                })

            # Si encontramos un "Sin:", lo asignamos al último plato detectado
            elif sin_match and last_plato is not None:
                nombre_sin = sin_match.group(1).strip()
                last_plato["sin"].append(nombre_sin)

        return order_data

    except Exception as e:
        print(f"Error al parsear el pedido: {e}")
        return {}  # Retorna un JSON vacío si hay un error