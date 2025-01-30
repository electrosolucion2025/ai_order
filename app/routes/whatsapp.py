import asyncio
import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi import Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.whatsapp import ProcessedMessage
from app.schemas.whatsapp import WhatsAppPayload
from app.services.whatsapp_service import process_whatsapp_message, send_message

router = APIRouter()
logger = logging.getLogger(__name__)


async def is_message_processed(db: AsyncSession, message_id: str) -> bool:
    result = await db.execute(select(ProcessedMessage).filter_by(message_id=message_id))
    return result.scalars().first() is not None


async def mark_message_as_processed(db: AsyncSession, message_id: str):
    processed_message = ProcessedMessage(message_id=message_id)
    db.add(processed_message)
    await db.commit()


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
                for message in messages:
                    message_id = message.get("id")
                    if await is_message_processed(db, message_id):
                        continue  # Skip already processed messages

                    from_number = message.get("from")
                    message_body = message.get("text", {}).get("body", "")
                    # Crear tareas para procesar cada mensaje
                    tasks.append(
                        process_whatsapp_message(from_number, message_body, db)
                    )
                    await mark_message_as_processed(db, message_id)

        await asyncio.gather(*tasks)

        return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logger.error(f"Error procesando el evento: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error procesando el evento")


@router.post("/send")
async def send_whatsapp_message(to: str, body: str):
    """
    Endpoint para enviar mensajes de WhatsApp.
    """
    await send_message(to, body)
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
