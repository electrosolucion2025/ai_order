import os

from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings

# Cargar variables desde el archivo .env
load_dotenv()


class Settings(BaseSettings):
    # Configuraciones generales
    PROJECT_NAME: str = "WhatsApp Chatbot"
    API_VERSION: str = "/api/v1"

    # Configuración de FastAPI
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"

    # Configuración de WhatsApp API
    WHATSAPP_API_URL: str = os.getenv("WHATSAPP_API_URL")
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN")

    # Configuración del webhook de WhatsApp
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN")

    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    # Configuración de BD
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Configuración de RedSys
    # REDSYS_URL: str = os.getenv("REDSYS_URL")
    # REDSYS_SECRET_KEY: str = os.getenv("REDSYS_SECRET_KEY")
    # REDSYS_MERCHANT_CODE: str = os.getenv("REDSYS_MERCHANT_CODE")

    class Config:
        case_sensitive = True
        env_file = ".env"


# Instancia global de configuración
settings = Settings()
