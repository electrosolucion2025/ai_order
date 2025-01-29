from pydantic import BaseModel, Field
from typing import List, Optional


class ExtraSchema(BaseModel):
    name: str = Field(..., example="Salsa de Queso")
    price: float = Field(..., example=1.5)
    available: bool = Field(..., example=True)


class MenuItemSchema(BaseModel):
    name: str = Field(..., example="Coca Cola")
    ingredients: Optional[str] = Field(None, example="Refresco")
    price: float = Field(..., example=2.2)
    available: bool = Field(..., example=True)
    extras: List[ExtraSchema] = []


class CategorySchema(BaseModel):
    name: str = Field(..., example="Bebidas")
    items: List[MenuItemSchema]


class MenuSchema(BaseModel):
    categories: List[CategorySchema]
