from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core.dependencies import engine
from app.routes import menu, whatsapp


async def lifespan(app: FastAPI):
    """
    Manejador de ciclo de vida para inicializar y limpiar recursos.
    """
    try:
        # Startup: Conectar y verificar la conexión a la base de datos
        async with engine.begin():
            print("Conexión a la base de datos establecida.")
    except SQLAlchemyError as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise e

    yield  # Yield vacío para manejar el ciclo de vida

    # Shutdown: Liberar recursos
    await engine.dispose()
    print("Conexión a la base de datos cerrada.")


def create_app() -> FastAPI:
    """
    Crear la aplicación FastAPI.
    """
    app = FastAPI(
        lifespan=lifespan,
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
    )
    # Registrar rutas
    app.include_router(
        menu.router, prefix=f"{settings.API_VERSION}/menu", tags=["Menu"]
    )
    app.include_router(
        whatsapp.router, prefix=f"{settings.API_VERSION}/whatsapp", tags=["WhatsApp"]
    )

    return app


app = create_app()


@app.get("/")
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
