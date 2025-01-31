import base64
import hashlib
import hmac
import requests

from fastapi import HTTPException
from redsys.client import RedirectClient
from redsys.constants import EUR, STANDARD_PAYMENT
from decimal import Decimal as D, ROUND_HALF_UP

from app.core.config import settings


class RedsysService:
    def __init__(self):
        """
        Inicializa el cliente de Redsys con la clave secreta.
        """
        self.client = RedirectClient(settings.REDSYS_SECRET_KEY)

    @staticmethod
    def generate_signature(key: str, data: str) -> str:
        """
        Genera la firma HMAC-SHA256 para Redsys
        """
        key_bytes = base64.b64decode(key)
        data_bytes = data.encode("utf-8")
        digest = hmac.new(key_bytes, data_bytes, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    def create_payment(self, order_id: str, amount: float):
        """
        Crea la estructura de datos para el pago y genera la firma.
        """
        merchant_parameters = {
            "amount": D(amount).quantize(
                D(".01"), ROUND_HALF_UP
            ),  # Redsys usa céntimos
            "order": order_id,
            "merchant_code": settings.REDSYS_MERCHANT_CODE,
            "transaction_type": STANDARD_PAYMENT,
            "currency": EUR,
            "terminal": "1",
            "merchant_url": settings.REDSYS_NOTIFICATION_URL,
            "merchant_name": "electroSolucion",
            "titular": "electroSolucion",
            "product_description": "Prueba de pago",
        }

        # Prepara la solicitud de Redsys
        prepared_request = self.client.prepare_request(merchant_parameters)

        # Decodifica los parámetros y firma para ser enviados al formulario
        prepared_request["Ds_MerchantParameters"] = prepared_request[
            "Ds_MerchantParameters"
        ].decode()
        prepared_request["Ds_Signature"] = prepared_request["Ds_Signature"].decode()

        return prepared_request

    def process_payment(self, order_id: str, amount: float, description: str):
        """
        Envia la solicitud de pago a Redsys y devuelve la URL de pago.
        """
        data = self.create_payment(order_id, amount)

        try:
            response = requests.post(settings.REDSYS_URL, data=data)
            response.raise_for_status()
            return response.url  # URL de pago

        except requests.RequestException as e:
            raise HTTPException(
                status_code=400, detail=f"Error en la solicitud de pago: {e}"
            )
