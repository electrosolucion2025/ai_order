import openai

from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.session_service import prepare_prompt, update_context, get_context

# Configurar la API de OpenAI
openai.api_key = settings.OPENAI_API_KEY


async def generate_openai_response(
    session_id: str, user_message: str, db: AsyncSession
):
    """
    Genera una respuesta de OpenAI en base al contexto de la sesión
    y el mensaje del usuario.
    """
    # Obtener el contexto actual de la sesión
    context = await get_context(session_id, db)

    # Construir el prompt con menú y historial de la conversación
    prompt = await prepare_prompt(context)

    # Enviar el prompt a OpenAI
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
    )

    bot_response = response.choices[0].message.content

    # Actualizar el contexto de la sesión
    context.setdefault("conversation", []).append(
        {"user": user_message, "bot": bot_response}
    )
    await update_context(session_id, {"conversation": context["conversation"]}, db)

    return bot_response
