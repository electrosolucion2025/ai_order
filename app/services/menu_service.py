from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Dict

from app.models.menu import Category, MenuItem


async def fetch_menu_as_json(tenant_id: int, db: AsyncSession) -> List[Dict]:
    """
    Consulta la base de datos y genera un menú en formato JSON.

    Parámetros:
        - tenant_id (int): ID del tenant para filtrar el menú.
        - db (AsyncSession): Sesión asíncrona de SQLAlchemy.

    Retorna:
        - List[Dict]: Lista con la estructura del menú en JSON.
    """
    # Consulta filtrando por tenant_id y cargando relaciones con selectinload
    result = await db.execute(
        select(Category)
        .where(Category.tenant_id == tenant_id)  # Filtrar por tenant_id
        .options(
            selectinload(Category.items).selectinload(
                MenuItem.extras
            )  # Cargar relaciones sin joins
        )
    )

    categories = result.scalars().all()

    # Filtrar items y extras en Python para evitar filtrado innecesario en SQL
    for category in categories:
        category.items = [
            item for item in category.items if item.tenant_id == tenant_id
        ]
        for item in category.items:
            item.extras = [
                extra for extra in item.extras if extra.tenant_id == tenant_id
            ]

    # Construcción del JSON del menú
    return [
        {
            "name": category.name,
            "items": [
                {
                    "name": item.name,
                    "ingredients": item.ingredients,
                    "price": item.price,
                    "available": item.available,
                    "extras": [
                        {
                            "name": extra.name,
                            "price": extra.price,
                            "available": extra.available,
                        }
                        for extra in item.extras  # Filtrado en Python
                    ],
                }
                for item in category.items  # Filtrado en Python
            ],
        }
        for category in categories
    ]
