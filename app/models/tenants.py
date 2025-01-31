from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base  # Importa la base declarativa

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False, unique=True)
    whatsapp_token = Column(String, nullable=False)  # 🔍 Token único para cada restaurante
    database_url = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=func.now())

    # **Nuevos campos para personalizar el chatbot**
    waiter_name = Column(String(50), nullable=True, default="Pepe")  # Nombre del camarero virtual
    business_name = Column(String(100), nullable=True, default="Template Name Bar")  # Nombre del restaurante
    table_number_min = Column(Integer, nullable=True, default=0)  # Número mínimo de mesa
    table_number_max = Column(Integer, nullable=True, default=10)  # Número máximo de mesa