from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # Nombre de la categoría
    items = relationship(
        "MenuItem", back_populates="category", cascade="all, delete-orphan"
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Nombre del producto
    ingredients = Column(Text)  # Ingredientes o descripción
    price = Column(Float, nullable=False)  # Precio del producto
    available = Column(Boolean, default=True)  # Disponibilidad del producto
    category_id = Column(Integer, ForeignKey("categories.id"))  # Relación con categoría
    extras = relationship(
        "Extra", back_populates="menu_item", cascade="all, delete-orphan"
    )
    category = relationship("Category", back_populates="items")


class Extra(Base):
    __tablename__ = "extras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Nombre del extra
    price = Column(Float, nullable=False)  # Precio del extra
    available = Column(Boolean, default=True)  # Disponibilidad del extra
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))  # Relación con producto
    menu_item = relationship("MenuItem", back_populates="extras")
