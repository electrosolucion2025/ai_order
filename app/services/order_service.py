from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderItem, Payment
from decimal import Decimal
from datetime import datetime, timezone


async def create_order(from_number: str, parsed_order: dict, tenant_id: int, db: AsyncSession):
    """
    Crea un pedido en la base de datos a partir de los datos extraídos.
    """
    try:
        # Extraemos la mesa y total
        table_number = parsed_order.get("mesa")
        total = Decimal(parsed_order.get("total", "0.0"))

        # 🔥 Convertimos la fecha a naive para evitar errores con PostgreSQL
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        # Crear nuevo pedido
        new_order = Order(
            table_number=table_number,
            customer_phone=from_number,
            total=total,
            status="pendiente",
            created_at=now_naive,
            updated_at=now_naive,
            tenant_id=tenant_id
        )

        db.add(new_order)
        await db.flush()  # Asegurar que new_order.id esté disponible

        # Verificar si hay productos en el pedido
        if not parsed_order.get("pedido"):
            raise ValueError("❌ El pedido no tiene productos.")

        # Generar ID de 12 digitos para el pedido
        order_id_formatted = str(new_order.id).zfill(12)

        # Guardar los productos del pedido
        for item in parsed_order["pedido"]:
            print(f"📝 Procesando item: {item}")  # Debug log

            item_obj = OrderItem(
                order_id=new_order.id,
                product_name=item.get("nombre", "Desconocido"),
                unit_price=Decimal(item.get("precio", "0.0")),
                quantity=item.get("cantidad", 1),
                subtotal=Decimal(item.get("subtotal", "0.0")),
                extras=str(item.get("extras", "")),  # Asegurar que no sea None
                exclusions=str(item.get("sin", "")),  # Asegurar que no sea None
                tenant_id=tenant_id
            )
            db.add(item_obj)

        await db.flush()  # 🔥 Asegurar que las líneas de pedido se registran antes del commit

        # Crear pago pendiente
        new_payment = Payment(
            order_id=new_order.id,
            status="pendiente",
            method="Redsys",
            transaction_id=None,
            amount=total,
            created_at=now_naive,  # Asegurar que la fecha es naive
            tenant_id=tenant_id
        )
        db.add(new_payment)

        await db.commit()  # ✅ Solo un commit al final

        return new_order, order_id_formatted

    except Exception as e:
        await db.rollback()
        print(f"❌ Error al guardar el pedido: {e}")
        return None
