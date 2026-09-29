from django.contrib import admin
from .models import NotificationLog, NotificationPreference


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["event_type", "channel", "recipient", "status", "reference", "created_at"]
    list_filter = ["channel", "status", "event_type"]
    search_fields = ["recipient", "reference"]
    readonly_fields = ["body_preview", "failure_reason", "created_at", "sent_at"]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "order_updates_email", "order_updates_sms", "marketing_emails"]


