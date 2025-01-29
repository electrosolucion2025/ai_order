from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SessionLogSchema(BaseModel):
    id: int
    session_id: int = Field(..., example=1)  # ID de la sesión
    user_message: str = Field(..., example="Hola, ¿puedes ayudarme?")
    bot_response: Optional[str] = Field(None, example="Claro, ¿en qué puedo ayudarte?")
    created_at: datetime = Field(..., example="2025-01-29T17:56:23")

    class Config:
        orm_mode = True

class SessionSchema(BaseModel):
    id: int
    user_id: str = Field(..., example="34607227417")  # Identificador del usuario
    context: Optional[str] = Field(None, example="{}")  # Contexto en JSON
    active: bool = Field(..., example=True)  # Si la sesión está activa
    created_at: datetime = Field(..., example="2025-01-29T17:56:23")
    updated_at: datetime = Field(..., example="2025-01-29T18:00:00")
    logs: List[SessionLogSchema] = []  # Relación con SessionLog
    message_logs: List[MessageLogSchema] = []  # Relación con MessageLog

    class Config:
        orm_mode = True
