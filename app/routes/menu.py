from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.menu import Category, MenuItem, Extra
from app.models.tenants import Tenant
from app.schemas.menu import MenuSchema

router = APIRouter()


@router.post("/upload", status_code=201)
async def upload_menu(menu: MenuSchema, db: AsyncSession = Depends(get_db)):
    """
    Endpoint para cargar un menú completo con categorías y productos en la base de datos.
    Verifica primero que el tenant_id sea válido y evita duplicados.
    """
    try:
        tenant_id = menu.tenant_id  # Extraemos tenant_id del JSON

        # 🔍 Verificar si el tenant_id existe en la base de datos
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=400,
                detail="❌ Tenant ID inválido. No existe en la base de datos.",
            )

        for category_data in menu.categories:
            # 🟢 Verificar si la categoría ya existe
            category_result = await db.execute(
                select(Category).where(
                    Category.name == category_data.name, Category.tenant_id == tenant_id
                )
            )
            category = category_result.scalar_one_or_none()

            if not category:
                # Si no existe, la creamos
                category = Category(name=category_data.name, tenant_id=tenant_id)
                db.add(category)
                await db.flush()  # Para obtener el ID de la categoría

            for item_data in category_data.items:
                # 🟢 Verificar si el producto ya existe en esa categoría
                item_result = await db.execute(
                    select(MenuItem).where(
                        MenuItem.name == item_data.name,
                        MenuItem.category_id == category.id,
                        MenuItem.tenant_id == tenant_id,
                    )
                )
                menu_item = item_result.scalar_one_or_none()

                if not menu_item:
                    # Si no existe, lo creamos
                    menu_item = MenuItem(
                        name=item_data.name,
                        ingredients=item_data.ingredients,
                        price=item_data.price,
                        available=item_data.available,
                        category_id=category.id,
                        tenant_id=tenant_id,
                    )
                    db.add(menu_item)
                    await db.flush()  # Para obtener el ID del producto

                for extra_data in item_data.extras:
                    # 🟢 Verificar si el extra ya existe en ese producto
                    extra_result = await db.execute(
                        select(Extra).where(
                            Extra.name == extra_data.name,
                            Extra.menu_item_id == menu_item.id,
                            Extra.tenant_id == tenant_id,
                        )
                    )
                    extra = extra_result.scalar_one_or_none()

                    if not extra:
                        # Si no existe, lo creamos
                        extra = Extra(
                            name=extra_data.name,
                            price=extra_data.price,
                            available=extra_data.available,
                            menu_item_id=menu_item.id,
                            tenant_id=tenant_id,
                        )
                        db.add(extra)

        # Confirmar cambios
        await db.commit()

        return {"message": "✅ Menú cargado con éxito sin duplicados!"}

    except HTTPException as he:
        raise he  # Relanzar excepciones HTTP para que se capturen correctamente

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error uploading menu: {e}")
