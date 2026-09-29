from django.contrib import admin
from .models import Warehouse, StockItem, StockMovement


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "is_active", "is_default"]


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ["__str__", "warehouse", "quantity", "reserved_quantity", "low_stock_threshold"]
    list_filter = ["warehouse"]
    search_fields = ["product__name", "variant__sku"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["stock_item", "movement_type", "quantity_change", "quantity_after", "created_at"]
    list_filter = ["movement_type"]
    readonly_fields = ["quantity_after", "created_at"]