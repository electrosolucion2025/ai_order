from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Order(Base):
    """
    Representa un pedido realizado en el restaurante.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    mesa = Column(Integer, nullable=False)  # Número de mesa asociada al pedido
    total = Column(Numeric(10, 2), nullable=False, default=0.0)  # Total del pedido
    status = Column(String, default="pendiente")  # Estado: pendiente, pagado, cancelado
    created_at = Column(DateTime, server_default=func.now())  # Fecha de creación del pedido

    # Relación con los ítems del pedido
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    # Relación con el pago del pedido
    payment = relationship("Payment", back_populates="order", uselist=False)

class OrderItem(Base):
    """
    Representa un producto dentro de un pedido.
    """
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)  # Pedido al que pertenece
    nombre = Column(String, nullable=False)  # Nombre del producto
    precio = Column(Numeric(10, 2), nullable=False)  # Precio unitario del producto
    cantidad = Column(Integer, nullable=False)  # Cantidad de productos comprados
    subtotal = Column(Numeric(10, 2), nullable=False)  # Precio total de esta línea

    # Relación con el pedido
    order = relationship("Order", back_populates="items")

class Payment(Base):
    """
    Representa el pago de un pedido a través de RedSys.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)  # Pedido asociado
    redsys_payment_id = Column(String, unique=True, nullable=True)  # ID de transacción de RedSys
    status = Column(String, default="pendiente")  # Estado del pago (pendiente, completado, fallido)
    created_at = Column(DateTime, server_default=func.now())  # Fecha del pago

    # Relación con el pedido
    order = relationship("Order", back_populates="payment")
