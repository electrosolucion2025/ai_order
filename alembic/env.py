from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from app.models.base import Base
from app.models.menu import *
from app.models.sessions import *
from app.models.whatsapp import *
from app.core.config import settings

# Configuración de logging
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData de los modelos
target_metadata = Base.metadata

# URL de la base de datos (asegúrate de que es síncrona)
DATABASE_URL = settings.DATABASE_URL.replace("asyncpg", "psycopg2")


def run_migrations_offline():
    """Ejecuta migraciones en modo 'offline'."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Ejecuta migraciones en modo 'online'."""
    connectable = create_engine(DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
