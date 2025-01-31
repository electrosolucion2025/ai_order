import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.dependencies import engine
from app.models.base import Base  # Asegúrate de importar tus modelos aquí
from app.models.menu import Category, MenuItem, Extra
from app.models.sessions import Session, SessionLog


async def init_db(engine: AsyncEngine):
    """
    Crea las tablas en la base de datos si no existen.
    """
    async with engine.begin() as conn:
        print("Creando tablas...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tablas creadas correctamente.")


if __name__ == "__main__":
    asyncio.run(init_db(engine))
