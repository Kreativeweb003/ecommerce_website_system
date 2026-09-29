from django.db import transaction
from django.core.exceptions import ValidationError
from notifications.services import notify_low_stock
from .models import Warehouse, StockItem, StockMovement


def get_default_warehouse():
    warehouse = Warehouse.objects.filter(is_default=True, is_active=True).first()
    if not warehouse:
        warehouse = Warehouse.objects.filter(is_active=True).first()
    return warehouse


def get_or_create_stock_item(*, warehouse, product=None, variant=None):
    if not product and not variant:
        raise ValidationError("Either product or variant must be provided.")

    lookup = {"warehouse": warehouse, "variant": variant} if variant else {"warehouse": warehouse, "product": product}
    stock_item, _ = StockItem.objects.get_or_create(**lookup)
    return stock_item




@transaction.atomic
def adjust_stock(*, stock_item, quantity_change, movement_type, reference="", note="", user=None):

    from wishlist.services import check_and_notify_price_drop
  
    stock_item = StockItem.objects.select_for_update().get(pk=stock_item.pk)

    new_quantity = stock_item.quantity + quantity_change
    if new_quantity < 0:
        raise ValidationError("Stock cannot go below zero.")

    was_out_of_stock = stock_item.is_out_of_stock

    stock_item.quantity = new_quantity

    should_send_alert = False
    if stock_item.is_low_stock and quantity_change < 0:
        cooldown_hours = getattr(settings, "LOW_STOCK_ALERT_COOLDOWN_HOURS", 24)
        cooldown_expired = (
            stock_item.last_low_stock_alert_at is None
            or (timezone.now() - stock_item.last_low_stock_alert_at).total_seconds() >= cooldown_hours * 3600
        )
        if cooldown_expired:
            stock_item.last_low_stock_alert_at = timezone.now()
            should_send_alert = True
    elif not stock_item.is_low_stock and stock_item.last_low_stock_alert_at is not None:
        stock_item.last_low_stock_alert_at = None

    stock_item.save(update_fields=["quantity", "last_low_stock_alert_at", "updated_at"])

    movement = StockMovement.objects.create(
        stock_item=stock_item,
        movement_type=movement_type,
        quantity_change=quantity_change,
        quantity_after=new_quantity,
        reference=reference,
        note=note,
        created_by=user,
    )

    if should_send_alert:
        notify_low_stock(stock_item=stock_item)

    if was_out_of_stock and not stock_item.is_out_of_stock:
        check_and_notify_back_in_stock(product=stock_item.product, variant=stock_item.variant)

    return movement


@transaction.atomic
def reserve_stock(*, stock_item, quantity):
    """Called when an item is added to cart / checkout starts."""
    stock_item = StockItem.objects.select_for_update().get(pk=stock_item.pk)

    if stock_item.available_quantity < quantity:
        raise ValidationError("Not enough stock available to reserve.")

    stock_item.reserved_quantity += quantity
    stock_item.save(update_fields=["reserved_quantity", "updated_at"])
    return stock_item


@transaction.atomic
def release_reserved_stock(*, stock_item, quantity):
    """Called when a cart expires or an order is cancelled before payment confirmation."""
    stock_item = StockItem.objects.select_for_update().get(pk=stock_item.pk)

    stock_item.reserved_quantity = max(stock_item.reserved_quantity - quantity, 0)
    stock_item.save(update_fields=["reserved_quantity", "updated_at"])
    return stock_item


@transaction.atomic
def fulfill_reserved_stock(*, stock_item, quantity, reference="", user=None):
    """Called when an order is confirmed/paid — converts reservation into an actual sale deduction."""
    stock_item = StockItem.objects.select_for_update().get(pk=stock_item.pk)

    stock_item.reserved_quantity = max(stock_item.reserved_quantity - quantity, 0)
    stock_item.save(update_fields=["reserved_quantity", "updated_at"])

    return adjust_stock(
        stock_item=stock_item,
        quantity_change=-quantity,
        movement_type="sale",
        reference=reference,
        user=user,
    )


def get_stock_for_product(*, product, warehouse=None):
    warehouse = warehouse or get_default_warehouse()
    return StockItem.objects.filter(product=product, warehouse=warehouse).first()


def get_stock_for_variant(*, variant, warehouse=None):
    warehouse = warehouse or get_default_warehouse()
    return StockItem.objects.filter(variant=variant, warehouse=warehouse).first()


def get_low_stock_items(*, warehouse=None):
    queryset = StockItem.objects.select_related("product", "variant", "warehouse")
    if warehouse:
        queryset = queryset.filter(warehouse=warehouse)
    return [item for item in queryset if item.is_low_stock]


def get_movement_history(*, stock_item):
    return stock_item.movements.select_related("created_by").all()




