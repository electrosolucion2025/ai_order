from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# Configurar la conexión a la base de datos
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Dependencia de sesión de base de datos
async def get_db():
    async with async_session() as session:
        yield session
