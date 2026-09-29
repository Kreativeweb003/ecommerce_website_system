from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "variant", "product_name", "sku", "unit_price", "quantity", "line_total"]


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["status", "note", "changed_by", "created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "user", "status", "total", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "email", "user__email"]
    readonly_fields = ["order_number", "subtotal", "total", "created_at", "updated_at"]
    inlines = [OrderItemInline, OrderStatusHistoryInline]

