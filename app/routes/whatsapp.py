import asyncio
import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi import Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.tenants import Tenant
from app.models.whatsapp import ProcessedMessage
from app.schemas.whatsapp import WhatsAppPayload
from app.services.whatsapp_service import (
    process_whatsapp_message,
    send_message,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def is_message_processed(db: AsyncSession, message_id: str, tenant_id: int) -> bool:
    """
    Verifica si un mensaje ya fue procesado, filtrando por tenant_id.
    """
    result = await db.execute(
        select(ProcessedMessage).filter_by(message_id=message_id, tenant_id=tenant_id)
    )
    return result.scalars().first() is not None


async def mark_message_as_processed(db: AsyncSession, message_id: str, tenant_id: int):
    """
    Marca un mensaje como procesado y lo asocia con un tenant específico.
    """
    processed_message = ProcessedMessage(message_id=message_id, tenant_id=tenant_id)
    db.add(processed_message)
    await db.commit()

async def get_tenant_id(db: AsyncSession, to_number: str) -> int:
    """
    Obtiene el tenant_id asociado a un número de teléfono.
    """
    result = await db.execute(select(Tenant.id).where(Tenant.phone_number == to_number))
    tenant_id = result.scalar_one_or_none()
    
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    return tenant_id

@router.post("/webhook")
async def whatsapp_webhook(
    payload: WhatsAppPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint para manejar mensajes entrantes de WhatsApp.
    """
    try:
        tasks = []
        for entry in payload.entry:
            for change in entry.changes:
                value = change.value
                messages = value.get("messages", [])
                
                # 📌 Obtener el número de destino al que escriben los clientes
                to_number = value.get("metadata", {}).get("display_phone_number")
                if not to_number:
                    continue # Skip messages without a destination number
                
                # 🔍 Obtener el tenant_id basado en el número de destino
                tenant_id = await get_tenant_id(db, to_number)
                
                for message in messages:
                    message_id = message.get("id")
                    if await is_message_processed(db, message_id, tenant_id):
                        continue  # Skip already processed messages

                    from_number = message.get("from")

                    # Verificar si el mensaje es un mensaje de texto
                    if "text" in message:
                        message_body = message["text"].get("body", "").strip()

                    # Verificar si el mensaje es un mensaje de audio
                    elif "audio" in message:
                        media_id = message["audio"].get("id")
                        if not media_id:
                            continue

                        message_body = {"type": "audio", "media_id": media_id}

                    else:
                        continue

                    # ✅ Crear tareas para procesar cada mensaje, incluyendo el `tenant_id`
                    tasks.append(
                        process_whatsapp_message(from_number, message_body, tenant_id, db)
                    )
                    await mark_message_as_processed(db, message_id, tenant_id)

        await asyncio.gather(*tasks)

        return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logger.error(f"Error procesando el evento: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error procesando el evento")


@router.post("/send")
async def send_whatsapp_message(to: str, body: str, tenant_id: int, db: AsyncSession = Depends(get_db)):
    """
    Endpoint para enviar mensajes de WhatsApp.
    """
    await send_message(to, body, tenant_id, db)
    return {"message": "Mensaje enviado correctamente"}


@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Verificación inicial del webhook para Meta.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return PlainTextResponse(challenge, status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Verificación fallida")
