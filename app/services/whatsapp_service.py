from sqlalchemy.ext.asyncio import AsyncSession

from app.services.session_service import (
    close_session,
    get_or_create_session,
    save_message_log,
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
    
    # Respuesta ficticia del bot
    bot_response = "¡Hola! Soy un bot de WhatsApp 🤖"

    # Guarda el log de la conversación
    await save_message_log(session.id, message_body, bot_response, db)

    # Envía la respuesta al usuario
    await send_whatsapp_message(from_number, bot_response)

    # Simular cierre de sesión (ejemplo: usuario envía "finalizar")
    if message_body.lower() == "finalizar":
        await close_session(from_number, db)
        await send_whatsapp_message(from_number, "¡Hasta luego! 👋")
