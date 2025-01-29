from fastapi import HTTPException
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

from app.services.session_service import (
    close_session,
    get_context,
    get_or_create_session,
    save_message_log,
    update_context,
)


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

    # Recupera el contexto de la sesión
    context = await get_context(session.id, db)

    # Respuesta ficticia del bot
    bot_response = "¡Hola! Soy un bot de WhatsApp 🤖"

    # Actualizar el contexto de la sesión
    context.setdefault("conversation", []).append(
        {"user": message_body, "bot": bot_response}
    )
    await update_context(session.id, {"conversation": context["conversation"]}, db)

    # Guarda el log de la conversación
    await save_message_log(session.id, message_body, bot_response, db)

    # Envía la respuesta al usuario
    await send_whatsapp_message(from_number, bot_response)

    # Simular cierre de sesión (ejemplo: usuario envía "finalizar")
    if message_body.lower() == "finalizar":
        context["conversation"].append({"bot": "¡Hasta luego! 👋"})
        await update_context(session.id, {"conversation": context["conversation"]}, db)
        await close_session(from_number, db)
        await send_whatsapp_message(from_number, "¡Hasta luego! 👋")

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