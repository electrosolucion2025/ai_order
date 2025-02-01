from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderItem, Payment
from decimal import Decimal
from datetime import datetime, timezone


async def create_order(from_number: str, parsed_order: dict, tenant_id: int, db: AsyncSession):
    """
    Crea un pedido en la base de datos con un número de pedido único por tenant.
    """
    try:
        from sqlalchemy import select, func
        from app.models.order import Order, OrderItem, Payment

        table_number = parsed_order.get("mesa")
        total = Decimal(parsed_order.get("total", "0.0"))

        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        # 🔍 Contar cuántos pedidos tiene este tenant para generar el número
        result = await db.execute(
            select(func.count(Order.id)).where(Order.tenant_id == tenant_id)
        )
        order_count = result.scalar() or 0

        # 🚀 Generar número de pedido de 12 dígitos, por ejemplo: 000000000001
        order_number = str(order_count + 1).zfill(12)

        # Crear nuevo pedido
        new_order = Order(
            order_number=order_number,
            table_number=table_number,
            customer_phone=from_number,
            total=total,
            status="pendiente",
            created_at=now_naive,
            updated_at=now_naive,
            tenant_id=tenant_id,
        )

        db.add(new_order)
        await db.flush()  # Asegurar que new_order.id esté disponible

        if not parsed_order.get("pedido"):
            raise ValueError("❌ El pedido no tiene productos.")

        for item in parsed_order["pedido"]:
            item_obj = OrderItem(
                order_id=new_order.id,
                product_name=item.get("nombre", "Desconocido"),
                unit_price=Decimal(item.get("precio", "0.0")),
                quantity=item.get("cantidad", 1),
                subtotal=Decimal(item.get("subtotal", "0.0")),
                extras=str(item.get("extras", "")),
                exclusions=str(item.get("sin", "")),
                tenant_id=tenant_id,
            )
            db.add(item_obj)

        await db.flush()

        new_payment = Payment(
            order_id=new_order.id,
            status="pendiente",
            method="Redsys",
            transaction_id=None,
            amount=total,
            created_at=now_naive,
            tenant_id=tenant_id,
        )
        db.add(new_payment)

        await db.commit()

        return new_order, order_number  # Retornamos el nuevo número de pedido

    except Exception as e:
        await db.rollback()
        print(f"❌ Error al guardar el pedido: {e}")
        return None
