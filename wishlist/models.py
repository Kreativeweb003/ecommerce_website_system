from django.db import models
from django.conf import settings

from products.models import Product, ProductVariant


class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wishlist_wishlist"

    def __str__(self):
        return f"Wishlist - {self.user.email}"

    @property
    def total_items(self):
        return self.items.count()


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name="wishlisted_by"
    )

    # Snapshotted at time of adding — lets us detect price drops later
    price_at_addition = models.DecimalField(max_digits=10, decimal_places=2)
    notified_price_drop = models.BooleanField(default=False)
    notified_back_in_stock = models.BooleanField(default=False)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wishlist_wishlist_item"
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "product"],
                condition=models.Q(variant__isnull=True),
                name="unique_wishlist_product_no_variant",
            ),
            models.UniqueConstraint(
                fields=["wishlist", "variant"],
                condition=models.Q(variant__isnull=False),
                name="unique_wishlist_variant",
            ),
        ]

    def __str__(self):
        item = self.variant if self.variant else self.product
        return f"{item} in {self.wishlist.user.email}'s wishlist"

    @property
    def current_price(self):
        return self.variant.price if self.variant else self.product.current_price

    @property
    def has_price_dropped(self):
        return self.current_price < self.price_at_addition

    @property
    def price_drop_amount(self):
        if self.has_price_dropped:
            return self.price_at_addition - self.current_price
        return 0


