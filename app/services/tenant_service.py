from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.tenants import Tenant


async def get_tenant_details(db: AsyncSession, tenant_id: int) -> dict:
    """
    Obtiene los detalles de personalización del tenant para configurar el chatbot.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalars().first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    return {
        "waiter_name": tenant.waiter_name or "Pepe",
        "business_name": tenant.business_name or "Template Name",
        "table_number_min": tenant.table_number_min or 0,
        "table_number_max": tenant.table_number_max or 10,
    }
