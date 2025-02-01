from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=False
    )  # Relación con el tenant
    order_number = Column(String(12), unique=True, index=True)  # Nuevo campo para el número de pedido
    table_number = Column(Integer, nullable=False)
    customer_phone = Column(String(15), nullable=True)
    status = Column(String, default="pendiente")
    total = Column(Numeric(10, 2), nullable=False)
    created_at = Column(
        DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=datetime.now(timezone.utc).replace(tzinfo=None),
    )

    order_items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", uselist=False, back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=False
    )  # Relación con el tenant
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    extras = Column(String, nullable=True)
    exclusions = Column(String, nullable=True)

    order = relationship("Order", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id"), nullable=False
    )  # Relación con el tenant
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(String, default="pendiente")
    method = Column(String, nullable=False)
    transaction_id = Column(String, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(
        DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None)
    )

    order = relationship("Order", back_populates="payment")
