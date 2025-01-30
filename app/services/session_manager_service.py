from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sessions import Session
from app.services.context_manager_service import initialize_context
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
