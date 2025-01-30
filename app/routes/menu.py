from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.menu import Category, MenuItem, Extra
from app.schemas.menu import MenuSchema

router = APIRouter()


@router.post("/upload", status_code=201)
async def upload_menu(menu: MenuSchema, db: AsyncSession = Depends(get_db)):
    """
    Endpoint para cargar un menú completo con categorías
    y productos en la base de datos.
    """
    try:
        for category_data in menu.categories:
            # Crear o buscar categoría
            category = Category(name=category_data.name)
            db.add(category)
            await db.flush()  # Para obtener el ID de la categoría

            # Añadir productos a la categoría
            for item_data in category_data.items:
                menu_item = MenuItem(
                    name=item_data.name,
                    ingredients=item_data.ingredients,
                    price=item_data.price,
                    available=item_data.available,
                    category_id=category.id,
                )
                db.add(menu_item)
                await db.flush()  # Para obtener el ID del producto

                # Añadir extras al producto
                for extra_data in item_data.extras:
                    extra = Extra(
                        name=extra_data.name,
                        price=extra_data.price,
                        available=extra_data.available,
                        menu_item_id=menu_item.id,
                    )
                    db.add(extra)

        # Confirmar cambios
        await db.commit()

        return {"message": "Menu uploaded successfully!"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error uploading menu: {e}")
