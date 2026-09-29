from django.db import models
from django.conf import settings

from orders.models import Order


class PaymentTransaction(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    )

    GATEWAY_CHOICES = (
        ("stripe", "Stripe"),
        ("paystack", "Paystack"),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_transactions")
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)

    gateway_reference = models.CharField(
        max_length=255, unique=True, help_text="Payment intent ID / charge ID / transaction reference from gateway."
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")

    raw_response = models.JSONField(blank=True, null=True, help_text="Full gateway response, for debugging/audit.")
    failure_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_transaction"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["gateway_reference"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.gateway} - {self.gateway_reference} ({self.status})"


class Refund(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    )

    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name="refunds")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")

    gateway_refund_reference = models.CharField(max_length=255, blank=True)
    raw_response = models.JSONField(blank=True, null=True)

    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_refund"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund of {self.amount} for {self.transaction.gateway_reference}"


class WebhookEvent(models.Model):
    """Logs every webhook received, to guarantee idempotency and provide an audit trail."""
    gateway = models.CharField(max_length=20, choices=PaymentTransaction.GATEWAY_CHOICES)
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments_webhook_event"
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.gateway} - {self.event_type} ({self.event_id})"




