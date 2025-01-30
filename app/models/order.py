from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(Integer, nullable=False)  # Número de mesa
    customer_phone = Column(String(15), nullable=False)  # Nuevo campo
    status = Column(String, default="pendiente")  # Estado: pendiente, pagado, cancelado
    total = Column(Numeric(10, 2), nullable=False)  # Total del pedido
    created_at = Column(
        DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=datetime.now(timezone.utc).replace(tzinfo=None),
    )

    # Relación con los elementos del pedido
    order_items = relationship("OrderItem", back_populates="order")

    # Relación con el pago
    payment = relationship("Payment", uselist=False, back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String, nullable=False)  # Nombre del producto
    unit_price = Column(Numeric(10, 2), nullable=False)  # Precio unitario
    quantity = Column(Integer, nullable=False)  # Cantidad
    subtotal = Column(Numeric(10, 2), nullable=False)  # Precio total por este ítem

    # Extras y modificaciones
    extras = Column(String, nullable=True)  # Guardaremos los extras como un JSON string
    exclusions = Column(String, nullable=True)  # Ingredientes excluidos

    # Relación con el pedido
    order = relationship("Order", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(String, default="pendiente")  # pendiente, completado, fallido
    method = Column(
        String, nullable=False
    )  # Método de pago (Redsys, efectivo, tarjeta)
    transaction_id = Column(String, nullable=True)  # ID de la transacción
    amount = Column(Numeric(10, 2), nullable=False)  # Monto pagado
    created_at = Column(
        DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None)
    )

    # Relación con la orden
    order = relationship("Order", back_populates="payment")
