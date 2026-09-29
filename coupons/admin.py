from django.contrib import admin
from .models import Coupon, CouponUsage


class CouponUsageInline(admin.TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ["user", "order_number", "discount_applied", "used_at"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "discount_value", "times_used", "usage_limit", "is_active", "valid_until"]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code"]
    inlines = [CouponUsageInline]