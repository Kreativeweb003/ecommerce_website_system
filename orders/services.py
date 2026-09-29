from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from cart.services import validate_cart_stock, clear_cart
from inventory.services import (
    get_stock_for_product, get_stock_for_variant,
    reserve_stock, release_reserved_stock, fulfill_reserved_stock,
)
from .models import Order, OrderItem, OrderStatusHistory
from coupons.services import validate_coupon, record_coupon_usage
from shipping.services import calculate_shipping_cost, get_cart_total_weight
from coupons.services import release_coupon_usage
from notifications.services import (
    notify_order_confirmed, notify_order_shipped,
    notify_order_delivered, notify_order_cancelled, notify_order_refunded,
)
from reviews.services import revoke_verified_purchase_if_unqualified
from django.core.cache import cache



def _get_stock_item(*, product, variant=None):
    return get_stock_for_variant(variant=variant) if variant else get_stock_for_product(product=product)



@transaction.atomic
def create_order_from_cart(*, cart, checkout_data, user=None):
    stock_problems = validate_cart_stock(cart=cart)
    if stock_problems:
        item_names = ", ".join(str(item.display_item) for item, _ in stock_problems)
        raise ValidationError(f"Some items are no longer available in the requested quantity: {item_names}")

    cart_items = list(cart.items.select_related("product", "variant"))
    if not cart_items:
        raise ValidationError("Cannot create an order from an empty cart.")

    subtotal = cart.subtotal

    # Shipping — validated server-side against the destination country, never trust a raw amount from the client
    total_weight_kg = get_cart_total_weight(cart=cart)
    shipping_method, shipping_cost = calculate_shipping_cost(
        method_id=checkout_data["shipping_method_id"],
        country=checkout_data["shipping_country"],
        subtotal=subtotal,
        total_weight_kg=total_weight_kg,
    )

    coupon = None
    discount_amount = Decimal("0")
    coupon_code = checkout_data.get("coupon_code", "").strip()
    if coupon_code:
        coupon, discount_amount = validate_coupon(code=coupon_code, subtotal=subtotal, user=user)

    total = subtotal + shipping_cost - discount_amount

    billing_same = checkout_data.get("billing_same_as_shipping", True)

    order = Order.objects.create(
        user=user,
        email=checkout_data["email"],
        phone_number=checkout_data["phone_number"],
        shipping_full_name=checkout_data["shipping_full_name"],
        shipping_street_address=checkout_data["shipping_street_address"],
        shipping_apartment=checkout_data.get("shipping_apartment", ""),
        shipping_city=checkout_data["shipping_city"],
        shipping_state=checkout_data["shipping_state"],
        shipping_postal_code=checkout_data["shipping_postal_code"],
        shipping_country=checkout_data["shipping_country"],
        billing_same_as_shipping=billing_same,
        billing_full_name=checkout_data["shipping_full_name"] if billing_same else checkout_data.get("billing_full_name", ""),
        billing_street_address=checkout_data["shipping_street_address"] if billing_same else checkout_data.get("billing_street_address", ""),
        billing_apartment=checkout_data["shipping_apartment"] if billing_same else checkout_data.get("billing_apartment", ""),
        billing_city=checkout_data["shipping_city"] if billing_same else checkout_data.get("billing_city", ""),
        billing_state=checkout_data["shipping_state"] if billing_same else checkout_data.get("billing_state", ""),
        billing_postal_code=checkout_data["shipping_postal_code"] if billing_same else checkout_data.get("billing_postal_code", ""),
        billing_country=checkout_data["shipping_country"] if billing_same else checkout_data.get("billing_country", ""),
        coupon_code=coupon.code if coupon else "",
        customer_note=checkout_data.get("customer_note", ""),
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        discount_amount=discount_amount,
        total=total,
    )

    reserved_stock_items = []
    try:
        for cart_item in cart_items:
            stock_item = _get_stock_item(product=cart_item.product, variant=cart_item.variant)
            if not stock_item:
                raise ValidationError(f"No stock record found for {cart_item.display_item}.")

            reserve_stock(stock_item=stock_item, quantity=cart_item.quantity)
            reserved_stock_items.append((stock_item, cart_item.quantity))

            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=cart_item.product.name,
                variant_description=str(cart_item.variant) if cart_item.variant else "",
                sku=cart_item.variant.sku if cart_item.variant else cart_item.product.sku,
                unit_price=cart_item.unit_price,
                quantity=cart_item.quantity,
                line_total=cart_item.total_price,
            )
    except ValidationError:
        for stock_item, quantity in reserved_stock_items:
            release_reserved_stock(stock_item=stock_item, quantity=quantity)
        raise

    if coupon:
        record_coupon_usage(coupon=coupon, order_number=order.order_number, discount_applied=discount_amount, user=user)

    OrderStatusHistory.objects.create(order=order, status="pending", note="Order created, awaiting payment.")

    clear_cart(cart=cart)

    cache.delete_many([f"dashboard:overview:{p}" for p in ("7d", "30d", "90d", "1y")])

    notify_order_confirmed(order=order)

    return order



@transaction.atomic
def mark_order_paid(*, order, user=None):
    """Called by the payments app once payment is confirmed. Converts reservations into real stock deductions."""
    if order.status != "pending":
        raise ValidationError("Only pending orders can be marked as paid.")

    for item in order.items.select_related("product", "variant"):
        stock_item = _get_stock_item(product=item.product, variant=item.variant)
        if stock_item:
            fulfill_reserved_stock(
                stock_item=stock_item, quantity=item.quantity, reference=order.order_number, user=user
            )

    order.status = "paid"
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at", "updated_at"])

    OrderStatusHistory.objects.create(order=order, status="paid", note="Payment confirmed.", changed_by=user)
    return order

  

@transaction.atomic
def update_order_status(*, order, new_status, note="", user=None):
    valid_transitions = {
        "pending": ["paid", "cancelled"],
        "paid": ["processing", "cancelled", "refunded"],
        "processing": ["shipped", "cancelled"],
        "shipped": ["delivered"],
        "delivered": ["refunded"],
        "cancelled": [],
        "refunded": [],
    }

    if new_status not in valid_transitions.get(order.status, []):
        raise ValidationError(f"Cannot transition order from '{order.status}' to '{new_status}'.")

    if new_status == "cancelled":
        return cancel_order(order=order, reason=note, user=user)

    order.status = new_status
    if new_status == "shipped":
        order.shipped_at = timezone.now()
    elif new_status == "delivered":
        order.delivered_at = timezone.now()

    order.save()
    OrderStatusHistory.objects.create(order=order, status=new_status, note=note, changed_by=user)

    if new_status == "shipped":
        notify_order_shipped(order=order)
    elif new_status == "delivered":
        notify_order_delivered(order=order)

    return order






@transaction.atomic
def cancel_order(*, order, reason="", user=None):
    if not order.can_be_cancelled:
        raise ValidationError("This order can no longer be cancelled.")

    for item in order.items.select_related("product", "variant"):
        stock_item = _get_stock_item(product=item.product, variant=item.variant)
        if not stock_item:
            continue
        if order.status == "pending":
            release_reserved_stock(stock_item=stock_item, quantity=item.quantity)
        else:
            from inventory.services import adjust_stock
            adjust_stock(
                stock_item=stock_item, quantity_change=item.quantity,
                movement_type="return", reference=order.order_number, user=user,
            )

    if order.coupon_code:
        release_coupon_usage(order_number=order.order_number)

    order.status = "cancelled"
    order.cancelled_at = timezone.now()
    order.save(update_fields=["status", "cancelled_at", "updated_at"])

    OrderStatusHistory.objects.create(order=order, status="cancelled", note=reason, changed_by=user)

    notify_order_cancelled(order=order, reason=reason)

    if order.user_id:
        for item in order.items.select_related("product"):
            if item.product:
                revoke_verified_purchase_if_unqualified(user=order.user, product=item.product)

    return order





def get_orders_for_user(*, user):
    return Order.objects.filter(user=user).prefetch_related("items")




def get_order_by_number(*, order_number, user=None):
    queryset = Order.objects.prefetch_related("items", "status_history")
    if user:
        queryset = queryset.filter(user=user)
    return queryset.get(order_number=order_number)




def get_all_orders(*, status=None):
    queryset = Order.objects.select_related("user").prefetch_related("items")
    if status:
        queryset = queryset.filter(status=status)
    return queryset