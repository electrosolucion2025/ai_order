from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from typing import AsyncGenerator

from app.core.config import settings
from app.core.dependencies import engine
from app.routes import menu

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from app.core.dependencies import engine
from app.core.config import settings
from app.routes import menu


async def lifespan(app: FastAPI):
    """
    Manejador de ciclo de vida para inicializar y limpiar recursos.
    """
    try:
        # Startup: Conectar y verificar la conexión a la base de datos
        async with engine.begin() as conn:
            print("Conexión a la base de datos establecida.")
            
    except SQLAlchemyError as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise e

    # Yield sin pasar el objeto `engine` directamente al contexto
    yield

    # Shutdown: Liberar recursos
    await engine.dispose()
    print("Conexión a la base de datos cerrada.")


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
)

# Registrar rutas
app.include_router(menu.router, prefix="/menu", tags=["Menu"])


@app.get("/")
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
)

app.include_router(menu.router, prefix=f"/{settings.API_VERSION}/menu", tags=["Menu"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)