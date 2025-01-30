from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Configuraciones generales
    PROJECT_NAME: str = Field("WhatsApp Chatbot", example="WhatsApp Chatbot")
    API_VERSION: str = Field("/api/v1", example="/api/v1")

    # Configuración de FastAPI
    SERVER_HOST: AnyHttpUrl = Field(
        "http://localhost:8000", example="http://localhost:8000"
    )

    # Configuración de WhatsApp API
    WHATSAPP_API_URL: str = Field(
        ..., env="WHATSAPP_API_URL", example="https://api.whatsapp.com/v1/messages"
    )
    WHATSAPP_TOKEN: str = Field(
        ..., env="WHATSAPP_TOKEN", example="your-whatsapp-token"
    )
    WHATSAPP_VERSION_API: str = Field(..., env="WHATSAPP_VERSION_API", example="v22.0")

    # Configuración del webhook de WhatsApp
    VERIFY_TOKEN: str = Field(..., env="VERIFY_TOKEN", example="your-verify-token")

    # Configuración de OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY", example="your-openai-key")

    # Configuración de BD
    DATABASE_URL: str = Field(
        "sqlite:///./test.db",
        env="DATABASE_URL",
        example="postgresql://user:password@localhost/db",
    )

    # Configuración de la aplicación
    HOST: str = Field("0.0.0.0", env="HOST", example="0.0.0.0")
    PORT: int = Field(8000, env="PORT", example=8000)

    class Config:
        case_sensitive = True
        env_file = ".env"


# Instancia global de configuración
settings = Settings()
