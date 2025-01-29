from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Identificador único del usuario (wa_id)
    context = Column(Text, nullable=True)  # Contexto en formato JSON (opcional)
    active = Column(Boolean, default=True)  # Indica si la sesión está activa
    created_at = Column(
        DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None)
    )  # Fecha de creación
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=datetime.now(timezone.utc).replace(tzinfo=None),
    )  # Última actualización
    logs = relationship("SessionLog", back_populates="session")


class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"))
    user_message = Column(Text, nullable=False)  # Mensaje enviado por el usuario
    bot_response = Column(Text, nullable=True)  # Respuesta del bot
    created_at = Column(
        DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None)
    )  # Fecha de creación
    session = relationship("Session", back_populates="logs")
