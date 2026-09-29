from django.contrib import admin
from .models import PaymentTransaction, Refund, WebhookEvent


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ["amount", "reason", "status", "gateway_refund_reference", "created_at"]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ["gateway_reference", "order", "gateway", "status", "amount", "created_at"]
    list_filter = ["gateway", "status"]
    search_fields = ["gateway_reference", "order__order_number"]
    inlines = [RefundInline]


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "gateway", "processed", "received_at"]
    list_filter = ["gateway", "processed"]
    readonly_fields = ["payload"]


