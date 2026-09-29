from django.contrib import admin
from .models import ShippingZone, ShippingMethod


class ShippingMethodInline(admin.TabularInline):
    model = ShippingMethod
    extra = 1


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ["name", "countries", "is_active"]
    inlines = [ShippingMethodInline]


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "zone", "rate_type", "flat_rate", "rate_per_kg", "is_active"]
    list_filter = ["rate_type", "is_active", "zone"]