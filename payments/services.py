from django.db import transaction
from django.core.exceptions import ValidationError
from reviews.services import revoke_verified_purchase_if_unqualified
from orders.services import mark_order_paid
from orders.models import Order
from .gateways import get_gateway
from .models import PaymentTransaction, Refund, WebhookEvent


def initiate_payment(*, order, gateway_name=None):
    """Starts a payment on the gateway and records a pending transaction."""
    gateway = get_gateway(gateway_name)

    result = gateway.create_payment_intent(
        amount=order.total, currency="USD", order=order,
    )

    payment_transaction = PaymentTransaction.objects.create(
        order=order,
        gateway=gateway.name,
        gateway_reference=result["reference"],
        status="pending",
        amount=order.total,
        currency="USD",
        raw_response=_safe_json(result["raw_response"]),
    )

    return payment_transaction, result["client_secret_or_redirect_url"]


def _safe_json(raw_response):
    """Gateway SDK objects aren't always plain dicts — normalize for JSONField storage."""
    if hasattr(raw_response, "to_dict"):
        return raw_response.to_dict()
    if isinstance(raw_response, dict):
        return raw_response
    return {"raw": str(raw_response)}


@transaction.atomic
def process_webhook_event(*, gateway_name, payload_body, headers):
    """
    Verifies signature, logs the event (idempotently), and updates the
    related PaymentTransaction + Order based on outcome.
    """
    gateway = get_gateway(gateway_name)

    if not gateway.verify_webhook_signature(payload_body=payload_body, headers=headers):
        raise ValidationError("Invalid webhook signature.")

    parsed = gateway.parse_webhook_event(payload_body=payload_body)

    # Idempotency: if we've already processed this exact event, skip silently.
    existing_event = WebhookEvent.objects.filter(event_id=parsed["event_id"]).first()
    if existing_event and existing_event.processed:
        return existing_event

    webhook_event, _ = WebhookEvent.objects.get_or_create(
        event_id=parsed["event_id"],
        defaults={
            "gateway": gateway.name,
            "event_type": parsed["event_type"],
            "payload": parsed["raw"],
        },
    )

    try:
        payment_transaction = PaymentTransaction.objects.select_for_update().get(
            gateway_reference=parsed["gateway_reference"]
        )
    except PaymentTransaction.DoesNotExist:
        webhook_event.processing_error = f"No matching transaction for reference {parsed['gateway_reference']}"
        webhook_event.save(update_fields=["processing_error"])
        return webhook_event

    _apply_transaction_status(payment_transaction=payment_transaction, new_status=parsed["status"])

    webhook_event.processed = True
    webhook_event.save(update_fields=["processed", "processing_error"])

    return webhook_event


def _apply_transaction_status(*, payment_transaction, new_status):
    if payment_transaction.status == new_status:
        return  # already applied — avoids double-processing on webhook retries

    payment_transaction.status = new_status
    payment_transaction.save(update_fields=["status", "updated_at"])

    order = payment_transaction.order

    if new_status == "succeeded" and order.status == "pending":
        mark_order_paid(order=order)
    elif new_status == "failed":
        pass  # order stays "pending" — customer can retry payment with a new transaction


def get_transaction_for_order(*, order):
    return PaymentTransaction.objects.filter(order=order).order_by("-created_at").first()




@transaction.atomic
def initiate_refund(*, order, amount=None, reason="", user=None):
    payment_transaction = PaymentTransaction.objects.filter(order=order, status="succeeded").first()
    if not payment_transaction:
        raise ValidationError("No successful payment found for this order to refund.")

    refund_amount = amount or order.total
    if refund_amount > payment_transaction.amount:
        raise ValidationError("Refund amount cannot exceed the original payment amount.")

    gateway = get_gateway(payment_transaction.gateway)
    result = gateway.create_refund(
        gateway_reference=payment_transaction.gateway_reference, amount=refund_amount
    )

    refund = Refund.objects.create(
        transaction=payment_transaction,
        amount=refund_amount,
        reason=reason,
        status=result["status"],
        gateway_refund_reference=result["reference"],
        raw_response=_safe_json(result["raw_response"]),
        initiated_by=user,
    )

    if result["status"] == "succeeded":
        payment_transaction.status = "refunded"
        payment_transaction.save(update_fields=["status", "updated_at"])
        notify_order_refunded(order=order, amount=refund_amount)

        if order.user_id:
            for item in order.items.select_related("product"):
                if item.product:
                    revoke_verified_purchase_if_unqualified(user=order.user, product=item.product)

    return refund


