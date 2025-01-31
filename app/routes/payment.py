from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.core.config import settings
from app.services.redsys_service import RedsysService

router = APIRouter()


# 🎯 Modelo para la solicitud de pago
class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    description: str


@router.get("/payment-form", response_class=HTMLResponse)
def render_payment_form(order_id: str, amount: float, user_id: str):
    """
    Renderiza el formulario de pago generado por Redsys.
    """
    try:
        # 🔥 Se crea una instancia de RedsysService
        redsys = RedsysService()
        form_html = start_payment(order_id, amount, user_id)
        return HTMLResponse(content=form_html, status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error generando el formulario: {str(e)}</h1>", status_code=500
        )


@router.post("/start", response_class=HTMLResponse)
def start_payment(order_id: str, amount: float, user_id: str):
    """
    Genera el formulario de pago para Redsys.
    """
    try:
        # Se crea una instancia de RedsysService dentro de la función
        redsys = RedsysService()

        # Obtener los parámetros de pago
        form_parameters = redsys.create_payment(order_id, amount)

        form_html = f"""
        <html>
            <head>
                <title>Redirigiendo al pago...</title>
            </head>
            <body onload="document.forms['redsysForm'].submit()">
                <p>Redirigiéndote a la pasarela de pago, por favor espera...</p>
                <form id="redsysForm" name="redsysForm" action="{settings.REDSYS_URL}" method="post">
                    <input type="hidden" name="Ds_SignatureVersion" value="HMAC_SHA256_V1" />
                    <input type="hidden" name="Ds_MerchantParameters" value="{form_parameters['Ds_MerchantParameters']}" />
                    <input type="hidden" name="Ds_Signature" value="{form_parameters['Ds_Signature']}" />
                    <noscript>
                        <p>Si no eres redirigido automáticamente, haz clic en el botón:</p>
                        <button type="submit">Pagar</button>
                    </noscript>
                </form>
            </body>
        </html>
        """
        return form_html

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
