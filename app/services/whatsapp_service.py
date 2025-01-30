import requests

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
