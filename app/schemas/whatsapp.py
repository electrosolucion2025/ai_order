from pydantic import BaseModel, Field
from typing import List, Optional


class WhatsAppMessage(BaseModel):
    from_: str = Field(
        ..., alias="from"
    )  # Alias para evitar conflictos con palabras clave de Python
    id: str
    timestamp: str
    text: Optional[dict] = None  # Mensaje de texto con el contenido


class WhatsAppChange(BaseModel):
    value: dict
    field: str


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]


class WhatsAppPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]
