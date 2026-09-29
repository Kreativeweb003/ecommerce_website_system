from django.core.exceptions import ValidationError
from .models import ShippingZone, ShippingMethod


def get_zone_for_country(*, country):
    """Finds the active zone whose country list includes the given country."""
    zones = ShippingZone.objects.filter(is_active=True)
    for zone in zones:
        if zone.covers_country(country):
            return zone
    return None


def get_available_methods_for_country(*, country):
    zone = get_zone_for_country(country=country)
    if not zone:
        return ShippingMethod.objects.none()
    return ShippingMethod.objects.filter(zone=zone, is_active=True)


def calculate_shipping_cost(*, method_id, country, subtotal, total_weight_kg=0):
    """
    Validates that the chosen method is actually valid for the destination country,
    then returns the calculated cost. Raises ValidationError otherwise.
    """
    available_methods = get_available_methods_for_country(country=country)
    method = available_methods.filter(pk=method_id).first()

    if not method:
        raise ValidationError("Selected shipping method is not available for this destination.")

    return method, method.calculate_cost(subtotal=subtotal, total_weight_kg=total_weight_kg)


def get_cart_total_weight(*, cart):
    """Sums product weight_kg * quantity across cart items. Missing weights count as 0."""
    total = 0
    for item in cart.items.select_related("product"):
        weight = item.product.weight_kg or 0
        total += weight * item.quantity
    return total


def get_cheapest_method_for_country(*, country, subtotal, total_weight_kg=0):
    """Useful as a sane default selection when the checkout page first loads."""
    methods = get_available_methods_for_country(country=country)
    if not methods.exists():
        return None, 0

    cheapest = None
    cheapest_cost = None
    for method in methods:
        cost = method.calculate_cost(subtotal=subtotal, total_weight_kg=total_weight_kg)
        if cheapest_cost is None or cost < cheapest_cost:
            cheapest = method
            cheapest_cost = cost

    return cheapest, cheapest_cost