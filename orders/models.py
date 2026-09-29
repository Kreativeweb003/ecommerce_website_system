from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid

from products.models import Product, ProductVariant


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Payment"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    )

    order_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="orders"
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")

    # Snapshotted contact + shipping/billing info (independent of accounts.Address, which can change)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)

    shipping_full_name = models.CharField(max_length=150)
    shipping_street_address = models.CharField(max_length=255)
    shipping_apartment = models.CharField(max_length=100, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)

    billing_full_name = models.CharField(max_length=150, blank=True)
    billing_street_address = models.CharField(max_length=255, blank=True)
    billing_apartment = models.CharField(max_length=100, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    billing_same_as_shipping = models.BooleanField(default=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    coupon_code = models.CharField(max_length=50, blank=True)

    customer_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orders_order"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        return f"ORD-{uuid.uuid4().hex[:10].upper()}"

    @property
    def is_paid(self):
        return self.status not in ("pending", "cancelled")

    @property
    def can_be_cancelled(self):
        return self.status in ("pending", "paid", "processing")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # Nullable so historical order items survive product deletion
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items"
    )

    # Snapshotted at time of purchase — product name/price may change later
    product_name = models.CharField(max_length=255)
    variant_description = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=100)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "orders_order_item"

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.order.order_number})"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=15, choices=Order.STATUS_CHOICES)
    note = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders_status_history"
        ordering = ["-created_at"]
        verbose_name_plural = "Order status histories"

    def __str__(self):
        return f"{self.order.order_number} -> {self.status}"



