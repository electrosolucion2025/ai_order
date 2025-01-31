import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sessions import SessionLog

# 🔥 Configuración del Logger
logger = logging.getLogger("log_manager_service")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


async def save_message_log(
    session_id: int,
    user_message: str,
    bot_response: str,
    tenant_id: int,
    db: AsyncSession,
):
    """
    Guarda un mensaje en la tabla de logs de sesión.
    """
    try:
        if db.in_transaction():  # Verifica si hay una transacción activa
            logger.warning("⚠️ Se ha detectado una transacción activa en la sesión.")

        else:
            async with db.begin():
                new_log = SessionLog(
                    session_id=session_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    tenant_id=tenant_id,
                )
                db.add(new_log)
                await db.flush()

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error al guardar el mensaje en logs: {e}", exc_info=True)
