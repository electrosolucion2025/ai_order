import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.dependencies import engine
from app.models.menu import Base  # Asegúrate de importar tus modelos aquí


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
