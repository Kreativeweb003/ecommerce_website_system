from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from products.models import Product, ProductVariant


class Warehouse(models.Model):
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_warehouse"
        ordering = ["-is_default", "name"]

    def __str__(self):
        return self.name


class StockItem(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_items")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name="stock_items"
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name="stock_items"
    )

    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    last_low_stock_alert_at = models.DateTimeField(
        null=True, blank=True, help_text="Set when a low-stock alert was last sent; cleared once restocked above threshold."
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_stock_item"
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "product"],
                condition=models.Q(variant__isnull=True),
                name="unique_product_stock_per_warehouse",
            ),
            models.UniqueConstraint(
                fields=["warehouse", "variant"],
                condition=models.Q(variant__isnull=False),
                name="unique_variant_stock_per_warehouse",
            ),
        ]

    def __str__(self):
        item = self.variant if self.variant else self.product
        return f"{item} @ {self.warehouse.name}: {self.quantity}"

    def clean(self):
        if not self.product and not self.variant:
            raise ValidationError("Either product or variant must be set.")
        if self.product and self.variant:
            raise ValidationError("Set only one of product or variant, not both.")

    @property
    def available_quantity(self):
        return max(self.quantity - self.reserved_quantity, 0)

    @property
    def is_low_stock(self):
        return self.available_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.available_quantity <= 0

      

class StockMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = (
        ("purchase", "Purchase / Restock"),
        ("sale", "Sale"),
        ("return", "Customer Return"),
        ("adjustment", "Manual Adjustment"),
        ("damage", "Damaged / Written Off"),
        ("transfer_in", "Transfer In"),
        ("transfer_out", "Transfer Out"),
    )

    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)

    quantity_change = models.IntegerField(help_text="Positive to add stock, negative to remove.")
    quantity_after = models.PositiveIntegerField()

    reference = models.CharField(max_length=100, blank=True, help_text="Order number, PO number, etc.")
    note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_stock_movement"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} ({self.quantity_change}) - {self.stock_item}"




