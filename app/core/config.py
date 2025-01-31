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
        ...,
        env="WHATSAPP_API_URL",
        example="https://api.whatsapp.com/v1/messages",
    )
    WHATSAPP_TOKEN: str = Field(
        ..., env="WHATSAPP_TOKEN", example="your-whatsapp-token"
    )
    WHATSAPP_VERSION_API: str = Field(..., env="WHATSAPP_VERSION_API", example="v22.0")

    # Configuración del webhook de WhatsApp
    VERIFY_TOKEN: str = Field(..., env="VERIFY_TOKEN", example="your-verify-token")

    # Configuración de OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY", example="your-openai-key")
    
    # Configuración de RedSys
    REDSYS_MERCHANT_CODE: str = Field(
        ..., env="REDSYS_MERCHANT_CODE", example="your-redsys-merchant-code"
    )
    REDSYS_SECRET_KEY: str = Field(
        ..., env="REDSYS_SECRET_KEY", example="your-redsys-secret-key"
    )
    REDSYS_TERMINAL: int = Field(..., env="REDSYS_TERMINAL", example=1)
    REDSYS_CURRENCY: int = Field(..., env="REDSYS_CURRENCY", example=978)
    REDSYS_URL: str = Field(
        ..., env="REDSYS_URL", example="https://sis.redsys.es/sis/realizarPago"
    )
    REDSYS_NOTIFICATION_URL: str = Field(
        ..., env="REDSYS_NOTIFICATION_URL", example="https://your-domain.com/payment-notification"
    )
    REDSYS_SUCCESS_URL: str = Field(
        ..., env="REDSYS_SUCCESS_URL", example="https://your-domain.com/payment-ok"
    )
    REDSYS_FAILURE_URL: str = Field(
        ..., env="REDSYS_FAILURE_URL", example="https://your-domain.com/payment-ko"
    )

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
