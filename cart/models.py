from django.db import models
from django.conf import settings

from products.models import Product, ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="cart"
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_cart"
        constraints = [
            models.UniqueConstraint(
                fields=["session_key"],
                condition=models.Q(user__isnull=True),
                name="unique_session_cart_for_guest",
            ),
        ]

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_key})"
        return f"Cart - {owner}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name="cart_items"
    )

    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_cart_item"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                condition=models.Q(variant__isnull=True),
                name="unique_cart_product_no_variant",
            ),
            models.UniqueConstraint(
                fields=["cart", "variant"],
                condition=models.Q(variant__isnull=False),
                name="unique_cart_variant",
            ),
        ]
        ordering = ["-added_at"]

    def __str__(self):
        item = self.variant if self.variant else self.product
        return f"{self.quantity} x {item}"

    @property
    def unit_price(self):
        return self.variant.price if self.variant else self.product.current_price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    @property
    def display_item(self):
        return self.variant if self.variant else self.product




