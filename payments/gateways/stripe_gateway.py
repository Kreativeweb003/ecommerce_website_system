import stripe
from django.conf import settings

from .base import BaseGateway


class StripeGateway(BaseGateway):
    name = "stripe"

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment_intent(self, *, amount, currency, order, metadata=None):
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe expects the smallest currency unit
            currency=currency.lower(),
            metadata={"order_number": order.order_number, **(metadata or {})},
        )
        return {
            "reference": intent.id,
            "client_secret_or_redirect_url": intent.client_secret,
            "raw_response": intent,
        }

    def verify_webhook_signature(self, *, payload_body, headers):
        try:
            stripe.Webhook.construct_event(
                payload_body, headers.get("Stripe-Signature"), settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except (stripe.error.SignatureVerificationError, ValueError):
            return False

    def parse_webhook_event(self, *, payload_body):
        import json
        event = json.loads(payload_body)
        data_object = event["data"]["object"]

        status_map = {
            "payment_intent.succeeded": "succeeded",
            "payment_intent.payment_failed": "failed",
            "payment_intent.canceled": "cancelled",
        }

        return {
            "event_id": event["id"],
            "event_type": event["type"],
            "gateway_reference": data_object.get("id"),
            "status": status_map.get(event["type"], "pending"),
            "raw": event,
        }

    def create_refund(self, *, gateway_reference, amount):
        refund = stripe.Refund.create(payment_intent=gateway_reference, amount=int(amount * 100))
        return {
            "reference": refund.id,
            "status": "succeeded" if refund.status == "succeeded" else "pending",
            "raw_response": refund,
        }



