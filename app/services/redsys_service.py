import base64
import hashlib
import hmac
import json
import requests

from fastapi import HTTPException
from redsys.client import RedirectClient
from redsys.constants import EUR, STANDARD_PAYMENT
from decimal import Decimal as D, ROUND_HALF_UP

from app.core.config import settings


class RedsysService:
    @staticmethod
    def generate_signature(key: str, data: str) -> str:
        """
        Genera la firma HMAC-SHA256 para Redsys
        """
        # Decodificar la clave y codificar los datos
        key_bytes = base64.b64decode(key)
        # Codificar los datos
        data_bytes = data.encode("utf-8")
        # Generar la firma
        digest = hmac.new(key_bytes, data_bytes, hashlib.sha256).digest()
        # Devolver la firma en base64
        return base64.b64encode(digest).decode("utf-8")
    
    @staticmethod
    def create_payment(order_id: str, amount: float, description: str):
        """
        Crea la estructura de datos para el pago y genera la firma
        """
        merchant_parameters = {
            "DS_MERCHANT_AMOUNT": int(D(amount * 100).to_integral_value(ROUND_HALF_UP) * 100),
            "DS_MERCHANT_ORDER": order_id,
            "DS_MERCHANT_MERCHANTCODE": settings.REDSYS_MERCHANT_CODE,
            "DS_MERCHANT_TRANSACTIONTYPE": STANDARD_PAYMENT,
            "DS_MERCHANT_CURRENCY": EUR,
            "DS_MERCHANT_TERMINAL": settings.REDSYS_TERMINAL,
            "DS_MERCHANT_MERCHANTURL": settings.REDSYS_NOTIFICATION_URL,
            "DS_MERCHANT_URLOK": settings.REDSYS_SUCCESS_URL,
            "DS_MERCHANT_URLKO": settings.REDSYS_FAILURE_URL,
            "DS_MERCHANT_PRODUCTDESCRIPTION": "Pago de prueba",
            "DS_MERCHANT_NAME": "ElectroSolucion",
            "DS_MERCHANT_TITULAR": "ElectroSolucion",
        }
        
        merchant_parameters_json = json.dumps(merchant_parameters)
        merchant_parameters_b64 = base64.b64encode(merchant_parameters_json.encode("utf-8")).decode("utf-8")
        
        signature = RedsysService.generate_signature(settings.REDSYS_SECRET_KEY, merchant_parameters_b64)
        
        return {
            "Ds_SignatureVersion": "HMAC_SHA256_V1",
            "Ds_MerchantParameters": merchant_parameters_b64,
            "Ds_Signature": signature,
        }
        
    @staticmethod
    def process_payment(order_id: str, amount: float, description: str):
        """
        Envia la solicitud de pago a Redsys y devuelve la URL de pago
        """
        data = RedsysService.create_payment(order_id, amount, description)
        
        try:
            response = requests.post(settings.REDSYS_URL, data=data)
            response.raise_for_status()
            
            return response.url # URL de pago
        
        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Error en la solicitud de pago: {e}")