import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sessions import Session


async def initialize_context(menu: dict) -> str:
    """
    Inicializa el contexto de la conversación.
    """
    if "menu" in menu:  # Evita duplicar la clave "menu"
        menu_data = menu["menu"]
    else:
        menu_data = menu

    return json.dumps(
        {
            "menu": menu_data,  # Para guardar el menú actual
            "conversation": [],  # Para guardar la conversación
            "current_order": None,  # Para guardar el pedido actual
        }
    )


async def get_context(session_id: int, tenant_id: int, db: AsyncSession) -> dict:
    """
    Obtiene el contexto de la conversación.
    """
    result = await db.execute(
        select(Session).filter(Session.id == session_id, Session.active, Session.tenant_id == tenant_id)
    )
    session = result.scalar()

    if session:
        return json.loads(session.context or "{}")

    return {}


async def update_context(session_id: int, new_context: dict, tenant_id: int, db: AsyncSession):
    """
    Actualiza el contexto de la conversación.
    """
    result = await db.execute(select(Session).filter(Session.id == session_id, Session.active, Session.tenant_id == tenant_id))
    session = result.scalar()

    if session:
        context = json.loads(session.context or "{}")
        context.update(new_context)
        session.context = json.dumps(context)
        await db.commit()
        await db.refresh(session)
