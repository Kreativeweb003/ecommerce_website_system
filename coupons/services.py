from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Coupon, CouponUsage


def validate_coupon(*, code, subtotal, user=None):
    """
    Validates a coupon code against current cart subtotal and user history.
    Returns the Coupon instance and calculated discount amount, or raises ValidationError.
    """
    code = code.upper().strip()

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        raise ValidationError("Invalid coupon code.")

    if not coupon.is_active:
        raise ValidationError("This coupon is no longer active.")

    if not coupon.has_started:
        raise ValidationError("This coupon is not yet valid.")

    if coupon.is_expired:
        raise ValidationError("This coupon has expired.")

    if coupon.is_usage_exhausted:
        raise ValidationError("This coupon has reached its usage limit.")

    if subtotal < coupon.minimum_order_value:
        raise ValidationError(f"Minimum order value of {coupon.minimum_order_value} required for this coupon.")

    if coupon.usage_limit_per_user is not None and user is not None:
        user_usage_count = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if user_usage_count >= coupon.usage_limit_per_user:
            raise ValidationError("You have already used this coupon the maximum number of times.")

    discount_amount = coupon.calculate_discount(subtotal=subtotal)
    return coupon, discount_amount


@transaction.atomic
def record_coupon_usage(*, coupon, order_number, discount_applied, user=None):
    """Called once the order is successfully created — locks the row to prevent race conditions on usage_limit."""
    coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)

    if coupon.is_usage_exhausted:
        raise ValidationError("This coupon has just reached its usage limit.")

    coupon.times_used += 1
    coupon.save(update_fields=["times_used"])

    return CouponUsage.objects.create(
        coupon=coupon, user=user, order_number=order_number, discount_applied=discount_applied
    )


def release_coupon_usage(*, order_number):
    """Called when an order using a coupon is cancelled — frees up the usage slot."""
    usage = CouponUsage.objects.filter(order_number=order_number).first()
    if not usage:
        return

    coupon = Coupon.objects.select_for_update().get(pk=usage.coupon_id)
    coupon.times_used = max(coupon.times_used - 1, 0)
    coupon.save(update_fields=["times_used"])

    usage.delete()


def get_active_coupons():
    return Coupon.objects.filter(is_active=True)