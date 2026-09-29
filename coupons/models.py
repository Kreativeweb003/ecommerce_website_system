from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("fixed", "Fixed Amount"),
        ("percentage", "Percentage"),
    )

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)

    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="percentage")
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Caps the discount for percentage coupons. Ignored for fixed coupons.",
    )

    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    usage_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text="Total number of times this coupon can be used. Blank = unlimited."
    )
    usage_limit_per_user = models.PositiveIntegerField(
        null=True, blank=True, help_text="Times a single user can use this coupon. Blank = unlimited."
    )
    times_used = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "coupons_coupon"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.valid_until:
            return timezone.now() > self.valid_until
        return False

    @property
    def has_started(self):
        return timezone.now() >= self.valid_from

    @property
    def is_usage_exhausted(self):
        if self.usage_limit is None:
            return False
        return self.times_used >= self.usage_limit

    def calculate_discount(self, *, subtotal):
        if self.discount_type == "fixed":
            discount = self.discount_value
        else:
            discount = subtotal * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)

        return min(discount, subtotal)


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="coupon_usages"
    )
    order_number = models.CharField(max_length=32)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "coupons_coupon_usage"
        ordering = ["-used_at"]

    def __str__(self):
        return f"{self.coupon.code} used on {self.order_number}"