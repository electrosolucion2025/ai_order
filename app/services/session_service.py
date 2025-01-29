from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.sessions import Session, SessionLog


async def get_or_create_session(user_id: str, db: AsyncSession):
    """
    Busca una sesión activa para el usuario o crea una nueva.
    """
    result = await db.execute(
        select(Session).filter(Session.user_id == user_id, Session.active == True)
    )
    session = result.scalar()

    if not session:
        session = Session(
            user_id=user_id,
            context=None,
            active=True,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    return session


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
        select(Session).filter(Session.user_id == user_id, Session.active == True)
    )
    session = result.scalar()

    if session:
        session.active = False

        # Actualizar el estado de los message_logs relacionados
        await db.execute(
            update(MessageLog)
            .where(MessageLog.session_id == session.id)
            .values(is_session_active=False)
        )

        await db.commit()
        await db.refresh(session)
