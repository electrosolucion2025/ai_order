import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.sessions import Session, SessionLog
from app.services.menu_service import fetch_menu_as_json


async def get_or_create_session(user_id: str, db: AsyncSession):
    """
    Busca una sesión activa para el usuario o crea una nueva.
    """
    result = await db.execute(
        select(Session).filter(Session.user_id == user_id, Session.active)
    )
    session = result.scalar()

    if not session:
        menu = await fetch_menu_as_json(db)

        session = Session(
            user_id=user_id,
            context=await initialize_context({"menu": menu}),
            active=True,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    return session


async def prepare_prompt(context: dict) -> str:
    """
    Prepara el prompt para el usuario.
    """
    prompt = "Eres Juan, un amable camarero. Este es tu menú en formato JSON:\n"
    prompt += f"{context.get('menu', {})}\n\n"
    prompt += "Aquí está el historial de la conversación:\n"
    for entry in context.get("conversation", []):
        prompt += f"Usuario: {entry['user']}\nBot: {entry['bot']}\n"
    return prompt


async def save_message_log(
    session_id: int, user_message: str, bot_response: str, db: AsyncSession
):
    """
    Guarda un log de la conversación.
    """
    log = SessionLog(
        session_id=session_id,
        user_message=user_message,
        bot_response=bot_response,
    )
    db.add(log)
    await db.commit()


async def close_session(user_id: str, db: AsyncSession):
    """
    Marca la sesión como inactiva y actualiza los registros relacionados.
    """
    result = await db.execute(
        select(Session).filter(Session.user_id == user_id, Session.active)
    )
    session = result.scalar()

    if session:
        session.active = False

        await db.commit()
        await db.refresh(session)


async def initialize_context(menu: dict) -> str:
    """
    Inicializa el contexto de la conversación.
    """
    return json.dumps(
        {
            "menu": menu,  # Para guardar el menú actual
            "conversation": [],  # Para guardar la conversación
            "current_order": None,  # Para guardar el pedido actual
        }
    )


async def get_context(session_id: int, db: AsyncSession) -> dict:
    """
    Obtiene el contexto de la conversación.
    """
    result = await db.execute(
        select(Session).filter(Session.id == session_id, Session.active)
    )
    session = result.scalar()

    if session:
        return json.loads(session.context or "{}")

    return {}


async def update_context(session_id: int, new_context: dict, db: AsyncSession):
    """
    Actualiza el contexto de la conversación.
    """
    result = await db.execute(select(Session).filter(Session.id == session_id))
    session = result.scalar()

    if session:
        context = json.loads(session.context or "{}")
        context.update(new_context)
        session.context = json.dumps(context)
        await db.commit()
        await db.refresh(session)
