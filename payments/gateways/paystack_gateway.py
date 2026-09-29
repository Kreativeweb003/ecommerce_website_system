import hashlib
import hmac
import json
import requests
from django.conf import settings

from .base import BaseGateway


class PaystackGateway(BaseGateway):
    name = "paystack"
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY

    def _headers(self):
        return {"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"}

    def create_payment_intent(self, *, amount, currency, order, metadata=None):
        response = requests.post(
            f"{self.BASE_URL}/transaction/initialize",
            headers=self._headers(),
            json={
                "email": order.email,
                "amount": int(amount * 100),  # kobo/cents
                "currency": currency.upper(),
                "reference": order.order_number,
                "metadata": {"order_number": order.order_number, **(metadata or {})},
            },
        )
        data = response.json()
        result = data.get("data", {})
        return {
            "reference": result.get("reference"),
            "client_secret_or_redirect_url": result.get("authorization_url"),
            "raw_response": data,
        }

    def verify_webhook_signature(self, *, payload_body, headers):
        computed_signature = hmac.new(
            self.secret_key.encode("utf-8"), payload_body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed_signature, headers.get("X-Paystack-Signature", ""))

    def parse_webhook_event(self, *, payload_body):
        event = json.loads(payload_body)
        data_object = event.get("data", {})

        status_map = {
            "charge.success": "succeeded",
            "charge.failed": "failed",
        }

        return {
            "event_id": data_object.get("id") or data_object.get("reference"),
            "event_type": event.get("event"),
            "gateway_reference": data_object.get("reference"),
            "status": status_map.get(event.get("event"), "pending"),
            "raw": event,
        }

    def create_refund(self, *, gateway_reference, amount):
        response = requests.post(
            f"{self.BASE_URL}/refund",
            headers=self._headers(),
            json={"transaction": gateway_reference, "amount": int(amount * 100)},
        )
        data = response.json()
        return {
            "reference": data.get("data", {}).get("id", ""),
            "status": "pending",
            "raw_response": data,
        }





