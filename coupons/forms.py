from django import forms
from .models import Coupon


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            "code", "description", "discount_type", "discount_value", "max_discount_amount",
            "minimum_order_value", "usage_limit", "usage_limit_per_user",
            "valid_from", "valid_until", "is_active",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_until": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ApplyCouponForm(forms.Form):
    code = forms.CharField(max_length=50)