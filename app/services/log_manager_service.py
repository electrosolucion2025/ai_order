from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sessions import SessionLog


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
