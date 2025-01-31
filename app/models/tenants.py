from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base  # Importa la base declarativa

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False, unique=True)
    database_url = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=func.now())
