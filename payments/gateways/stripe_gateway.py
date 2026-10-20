import json
import time

import stripe
from django.conf import settings
from django.urls import reverse

from .base import BaseGateway


class StripeGateway(BaseGateway):
    name = "stripe"

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment_intent(self, *, amount, currency, order, metadata=None):
        status_url = f"{settings.SITE_URL}{reverse('payments:payment_status', args=[order.order_number])}"
        expiry_minutes = max(30, getattr(settings, "PENDING_ORDER_EXPIRY_MINUTES", 60))  # Stripe minimum is 30

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": f"Order {order.order_number}"},
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }],
            customer_email=order.email,
            client_reference_id=order.order_number,
            metadata={"order_number": order.order_number, **(metadata or {})},
            success_url=status_url,
            cancel_url=status_url,
            expires_at=int(time.time()) + expiry_minutes * 60,
        )
        return {"reference": session.id, "client_secret_or_redirect_url": session.url, "raw_response": session}

    def verify_webhook_signature(self, *, payload_body, headers):
        try:
            stripe.Webhook.construct_event(
                payload_body, headers.get("Stripe-Signature"), settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except (stripe.SignatureVerificationError, ValueError):
            return False

    def parse_webhook_event(self, *, payload_body):
        event = json.loads(payload_body)
        data_object = event["data"]["object"]

        status_map = {
            "checkout.session.completed": "succeeded" if data_object.get("payment_status") == "paid" else "pending",
            "checkout.session.async_payment_succeeded": "succeeded",
            "checkout.session.async_payment_failed": "failed",
            "checkout.session.expired": "cancelled",
        }

        return {
            "event_id": event["id"],
            "event_type": event["type"],
            "gateway_reference": data_object.get("id"),  # the Checkout Session id we stored
            "status": status_map.get(event["type"], "pending"),
            "raw": event,
        }

    def create_refund(self, *, gateway_reference, amount):
        session = stripe.checkout.Session.retrieve(gateway_reference)
        refund = stripe.Refund.create(payment_intent=session.payment_intent, amount=int(amount * 100))
        return {
            "reference": refund.id,
            "status": "succeeded" if refund.status == "succeeded" else "pending",
            "raw_response": refund,
        }




  