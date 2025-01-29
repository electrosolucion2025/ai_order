import json
import requests

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.config import settings

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Endpoint para manejar mensajes entrantes de WhatsApp.
    """
    try:
        payload = await request.json()
        print(f"Payload recibido: {json.dumps(payload, indent=4)}")

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value")
                messages = value.get("messages", [])
                for message in messages:
                    from_number = message.get("from")
                    message_body = message.get("text", {}).get("body", "")
                    print(f"Mensaje de {from_number}: {message_body}")
                    # Aquí puedes procesar el mensaje o enviar una respuesta

        return {"message": "Evento recibido correctamente"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando el evento: {e}")


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
