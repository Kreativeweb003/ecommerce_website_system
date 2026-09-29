from django.db import models
from django.core.validators import MinValueValidator


class ShippingZone(models.Model):
    """Groups countries/regions that share the same shipping methods and rates."""
    name = models.CharField(max_length=150)
    countries = models.JSONField(
        default=list, help_text="List of country names/codes covered by this zone, e.g. ['US', 'CA']"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shipping_zone"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def covers_country(self, country):
        return country.strip().upper() in [c.strip().upper() for c in self.countries]


class ShippingMethod(models.Model):
    RATE_TYPE_CHOICES = (
        ("flat", "Flat Rate"),
        ("weight_based", "Weight Based"),
        ("free", "Free Shipping"),
    )

    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name="methods")
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)

    rate_type = models.CharField(max_length=15, choices=RATE_TYPE_CHOICES, default="flat")

    flat_rate = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    rate_per_kg = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)],
        help_text="Used only when rate_type is weight_based.",
    )
    base_rate = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)],
        help_text="Starting charge added to weight-based calculation.",
    )

    free_shipping_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="If order subtotal meets/exceeds this, shipping becomes free regardless of rate_type.",
    )

    estimated_days_min = models.PositiveIntegerField(default=1)
    estimated_days_max = models.PositiveIntegerField(default=7)

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "shipping_method"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.zone.name})"

    def calculate_cost(self, *, subtotal, total_weight_kg=0):
        if self.free_shipping_threshold is not None and subtotal >= self.free_shipping_threshold:
            return 0

        if self.rate_type == "free":
            return 0
        elif self.rate_type == "flat":
            return self.flat_rate
        elif self.rate_type == "weight_based":
            return self.base_rate + (self.rate_per_kg * total_weight_kg)

        return 0

    @property
    def estimated_delivery_label(self):
        if self.estimated_days_min == self.estimated_days_max:
            return f"{self.estimated_days_min} day(s)"
        return f"{self.estimated_days_min}-{self.estimated_days_max} days"



