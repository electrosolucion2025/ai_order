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
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=False
    )  # Relación con el tenant
    name = Column(String, nullable=False)
    items = relationship(
        "MenuItem", back_populates="category", cascade="all, delete-orphan"
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=False
    )  # Relación con el tenant
    name = Column(String, nullable=False)
    ingredients = Column(Text)
    price = Column(Float, nullable=False)
    available = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    extras = relationship(
        "Extra", back_populates="menu_item", cascade="all, delete-orphan"
    )
    category = relationship("Category", back_populates="items")


class Extra(Base):
    __tablename__ = "extras"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=False
    )  # Relación con el tenant
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    available = Column(Boolean, default=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    menu_item = relationship("MenuItem", back_populates="extras")
