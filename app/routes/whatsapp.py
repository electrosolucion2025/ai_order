import asyncio
import logging
import requests

from fastapi import APIRouter, Request, HTTPException
from fastapi import Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.whatsapp import WhatsAppPayload
from app.services.whatsapp_service import process_whatsapp_message
from app.core.dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


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
                    from_number = message.get("from")
                    message_body = message.get("text", {}).get("body", "")
                    # Crear tareas para procesar cada mensaje
                    tasks.append(
                        process_whatsapp_message(from_number, message_body, db)
                    )

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

    if response.status_code == 200:
        return {"message": "Mensaje enviado correctamente"}

    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error enviando mensaje: {response.text}",
        )


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
