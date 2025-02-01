import base64
import json
from urllib.parse import parse_qs, unquote
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.services.redsys_service import RedsysService

router = APIRouter()


@router.get("/payment-form", response_class=HTMLResponse)
def render_payment_form(order_id: str, amount: float, tenant_id: int):
    """
    Renderiza el formulario de pago generado por Redsys.
    """
    try:
        # 🔥 Se crea una instancia de RedsysService
        redsys = RedsysService()
        form_html = start_payment(order_id, amount, tenant_id)
        return HTMLResponse(content=form_html, status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error generando el formulario: {str(e)}</h1>", status_code=500
        )


@router.post("/start", response_class=HTMLResponse)
def start_payment(order_id: str, amount: float, tenant_id: int):
    """
    Genera el formulario de pago para Redsys.
    """
    try:
        # Se crea una instancia de RedsysService dentro de la función
        redsys = RedsysService()

        # Obtener los parámetros de pago
        form_parameters = redsys.create_payment(order_id, amount, tenant_id)

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

@router.post("/redsys/notification")
async def notify(request: Request):
    """
    Maneja las notificaciones de Redsys después del pago.
    """
    try:
        body = await request.body()
        print(f"🔍 Cuerpo recibido: {body.decode('utf-8')}")

        form_data = parse_qs(body.decode("utf-8"))
        print(f"🔍 Formulario recibido: {form_data}")

        merchant_parameters = form_data.get("Ds_MerchantParameters", [None])[0]
        if not merchant_parameters:
            raise HTTPException(status_code=400, detail="Missing Ds_MerchantParameters")

        decoded_params = decode_merchant_parameters(merchant_parameters)
        print(f"🔍 Parámetros decodificados: {decoded_params}")

        ds_response = int(decoded_params.get("Ds_Response", -1))
        if 0 <= ds_response <= 99:
            return await payment_response_success(body)
        elif ds_response == 9915:
            print("🚫 Usuario canceló el pago")
        else:
            print("❌ Error en el pago")

    except Exception as e:
        print(f"❌ Error en notificación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
def decode_merchant_parameters(merchant_parameters: str):
    decoded = base64.b64decode(merchant_parameters).decode("utf-8")
    return json.loads(decoded)

@router.post("/redsys/success")
async def payment_response_success(body: bytes):
    """
    Maneja las respuestas exitosas de Redsys.
    """
    try:
        parsed_body = parse_qs(body.decode("utf-8"))
        print(f"🔍 Datos del cuerpo recibido: {parsed_body}")

        Ds_MerchantParameters = parsed_body.get("Ds_MerchantParameters", [None])[0]
        Ds_Signature = parsed_body.get("Ds_Signature", [None])[0]

        if not Ds_MerchantParameters or not Ds_Signature:
            raise HTTPException(status_code=400, detail="Faltan parámetros requeridos")

        decoded_parameters = base64.b64decode(Ds_MerchantParameters).decode("utf-8")
        parameters = json.loads(decoded_parameters)
        print(f"🔍 Parámetros decodificados: {parameters}")

        merchant_data = parameters.get("Ds_MerchantData")
        if not merchant_data:
            raise HTTPException(status_code=400, detail="Ds_MerchantData no encontrado")

        print(f"🔍 Merchant Data recibido (codificado): {merchant_data}")

        # ✅ Decodificar el merchant_data de URL encoding
        decoded_merchant_data = unquote(merchant_data)
        print(f"🔍 Merchant Data decodificado: {decoded_merchant_data}")

        # ✅ Separar por '|'
        try:
            order_id, tenant_id = decoded_merchant_data.split("|")
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"Error al separar merchant_data: {ve}")

        print(f"✅✅✅✅✅✅✅✅ Pedido ID: {order_id}, Tenant ID: {tenant_id}")

        return {"message": "Pago exitoso", "order_id": order_id, "tenant_id": tenant_id}

    except Exception as e:
        print(f"❌ Error en payment_response_success: {e}")
        raise HTTPException(status_code=400, detail=str(e))
