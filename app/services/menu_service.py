from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.menu import Category, MenuItem
from typing import List, Dict


async def fetch_menu_as_json(db: AsyncSession) -> List[Dict]:
    """
    Consulta la base de datos y genera un menú en formato JSON.
    """
    result = await db.execute(
        select(Category).options(
            selectinload(Category.items).selectinload(MenuItem.extras)
        )
    )
    categories = result.scalars().all()

    menu = []
    for category in categories:
        menu.append(
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
                            for extra in item.extras
                        ],
                    }
                    for item in category.items
                ],
            }
        )
    return menu
