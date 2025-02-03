import base64
import json

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from urllib.parse import parse_qs, unquote
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.models.order import Order, Payment
from app.routes.whatsapp import send_whatsapp_message
from app.services.database_service import DatabaseService
from app.services.redsys_service import RedsysService
from app.services.session_manager_service import close_session

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
            return await payment_response_failure(body)
        
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
        # Inicializar DatabaseService
        db_service = DatabaseService()
        db = await db_service.get_session()
        
        parsed_body = parse_qs(body.decode("utf-8"))

        Ds_MerchantParameters = parsed_body.get("Ds_MerchantParameters", [None])[0]
        Ds_Signature = parsed_body.get("Ds_Signature", [None])[0]

        if not Ds_MerchantParameters or not Ds_Signature:
            raise HTTPException(status_code=400, detail="Faltan parámetros requeridos")

        decoded_parameters = base64.b64decode(Ds_MerchantParameters).decode("utf-8")
        parameters = json.loads(decoded_parameters)

        merchant_data = parameters.get("Ds_MerchantData")
        if not merchant_data:
            raise HTTPException(status_code=400, detail="Ds_MerchantData no encontrado")

        # ✅ Decodificar el merchant_data de URL encoding
        decoded_merchant_data = unquote(merchant_data)

        # ✅ Separar por '|'
        try:
            order_id, tenant_id = decoded_merchant_data.split("|")
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"Error al separar merchant_data: {ve}")

        print(f"✅✅✅✅✅✅✅✅ Pedido ID: {order_id}, Tenant ID: {tenant_id}")
        
        # ✅ Convertir a enteros
        order_id_str = str(order_id)
        tenant_id = int(tenant_id)
        
        # ✅ Consulta asincrónica
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.order_items), selectinload(Order.payment))
            .where(Order.order_number == order_id_str, Order.tenant_id == tenant_id)
        )
        order = result.scalars().first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # ✅ Actualizar el estado del pedido y del payment
        await db.execute(
            update(Order)
            .where(Order.order_number == order_id_str, Order.tenant_id == tenant_id)
            .values(status="Pagado")
        )
            
        # ✅ Actualizar el estado del pago directamente en la base de datos
        await db.execute(
            update(Payment)
            .where(Payment.order_id == order.id)
            .values(status="Pagado")
        )
        
        # ✅ Confirmar la transacción
        await db.commit()
        
        # ✅ Enviar mensaje de confirmación al usuario
        await send_whatsapp_message(
            f"+{order.customer_phone}",
            "¡Gracias por tu pago! 🎉 Ha sido confirmado con exito.",
            tenant_id=tenant_id,
        )
        
        # ✅ Finalizar la sesión
        await close_session(order.customer_phone, tenant_id, db)
        
        return {"message": "Pago exitoso"}

    except ValueError:
        raise HTTPException(status_code=400, detail="ID de pedido o Tenant no válido")

    except Exception as e:
        print(f"❌ Error en payment_response_success: {e}")
        await db.rollback()  # Revertir la transacción en caso de error
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/redsys/error")
async def payment_response_failure(body: bytes):
    """
    Maneja la respuesta de Redsys después de un fallo en el pago.
    """
    try:
        # Inicializar DatabaseService
        db_service = DatabaseService()
        db = await db_service.get_session()

        # Parsear los datos de Redsys
        parsed_body = parse_qs(body.decode("utf-8"))

        Ds_MerchantParameters = parsed_body.get("Ds_MerchantParameters", [None])[0]
        Ds_Signature = parsed_body.get("Ds_Signature", [None])[0]

        if not Ds_MerchantParameters or not Ds_Signature:
            raise HTTPException(status_code=400, detail="Faltan parámetros requeridos")

        # Decodificar parámetros
        decoded_parameters = base64.b64decode(Ds_MerchantParameters).decode("utf-8")
        parameters = json.loads(decoded_parameters)

        # Obtener merchant_data (contiene order_number y tenant_id)
        merchant_data = parameters.get("Ds_MerchantData")
        if not merchant_data:
            raise HTTPException(status_code=400, detail="Ds_MerchantData no encontrado")

        decoded_merchant_data = unquote(merchant_data)
        order_id, tenant_id = decoded_merchant_data.split("|")

        # ✅ Convertir a enteros
        order_id_str = str(order_id)
        tenant_id = int(tenant_id)
        
        # ✅ Consulta asincrónica
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.order_items), selectinload(Order.payment))
            .where(Order.order_number == order_id_str, Order.tenant_id == tenant_id)
        )
        order = result.scalars().first()

        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        # Actualizar el estado del pedido a "Fallido"
        await db.execute(
            update(Order)
            .where(Order.order_number == order_id_str, Order.tenant_id == tenant_id)
            .values(status="Fallido")
        )

        # Actualizar el estado del pago a "Fallido"
        if order.payment:
            await db.execute(
                update(Payment)
                .where(Payment.order_id == order.id)
                .values(status="Fallido")
            )
        else:
            raise HTTPException(status_code=404, detail="Pago no encontrado")

        # Confirmar la transacción
        await db.commit()

        error_message = "Lo sentimos, tu pago ha fallado. Por favor, intenta de nuevo más tarde o contacta con tu banco."

        try:
            await send_whatsapp_message(
                f"+{order.customer_phone}",
                "😞 Lo sentimos, tu pago ha fallado. Por favor, intenta de nuevo más tarde o contacta con tu banco.",
                tenant_id=tenant_id,
            )
            
            await send_whatsapp_message(
                f"+{order.customer_phone}",
                "Si deseas solicitar un nuevo link de pago, por favor escribe 'Repíteme el resumen' y te enviaremos uno nuevo.",
                tenant_id=tenant_id,
            )
        except Exception as whatsapp_error:
            print(f"Error enviando mensaje por WhatsApp: {whatsapp_error}")
            raise HTTPException(status_code=500, detail=f"Error enviando mensaje por WhatsApp: {whatsapp_error}")

        return {"status": "failure", "message": error_message}

    except Exception as e:
        print(f"❌ Error en payment_response_failure: {e}")
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))