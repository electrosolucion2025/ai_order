from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)  # Relación con el tenant
    user_id = Column(String, nullable=False)
    context = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None), onupdate=datetime.now(timezone.utc).replace(tzinfo=None))

    logs = relationship("SessionLog", back_populates="session")


class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)  # Relación con el tenant
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"))
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None))

    session = relationship("Session", back_populates="logs")
