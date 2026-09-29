from django.db import models
from django.conf import settings


class NotificationLog(models.Model):
    """Audit trail of every notification attempted — lets support staff see what was actually sent."""
    CHANNEL_CHOICES = (
        ("email", "Email"),
        ("sms", "SMS"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    EVENT_CHOICES = (
        ("order_confirmed", "Order Confirmed"),
        ("payment_failed", "Payment Failed"),
        ("order_shipped", "Order Shipped"),
        ("order_delivered", "Order Delivered"),
        ("order_cancelled", "Order Cancelled"),
        ("order_refunded", "Order Refunded"),
        ("low_stock_alert", "Low Stock Alert"),
        ("welcome", "Welcome Email"),
        ("password_changed", "Password Changed"),
        ("wishlist_price_drop", "Wishlist Price Drop"),
        ("wishlist_back_in_stock", "Wishlist Back In Stock"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default="email")
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)

    recipient = models.CharField(max_length=255, help_text="Email address or phone number.")
    subject = models.CharField(max_length=255, blank=True)
    body_preview = models.TextField(blank=True)

    reference = models.CharField(max_length=100, blank=True, help_text="Order number or other related object ref.")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    failure_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.recipient} ({self.status})"


class NotificationPreference(models.Model):
    """Per-user opt-in/opt-out for non-transactional notification types."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference"
    )
    order_updates_email = models.BooleanField(default=True)
    order_updates_sms = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=True)

    class Meta:
        db_table = "notifications_preference"

    def __str__(self):
        return f"Preferences for {self.user.email}"



