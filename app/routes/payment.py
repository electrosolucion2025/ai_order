from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.services.redsys_service import RedsysService

router = APIRouter()

# 🎯 Modelo para la solicitud de pago
class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    description: str

@router.post("/create-payment")
async def create_payment(payment_data: PaymentRequest, db: AsyncSession = Depends(get_db)):
    """
    Crea un pago en Redsys basado en los datos proporcionados
    """
    try:
        payment_info = RedsysService.create_payment(
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            description=payment_data.description
        )
        
        return {"payment_url": settings.REDSYS_URL, "data": payment_info}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el pago: {e}")