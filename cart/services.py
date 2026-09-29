from django.core.exceptions import ValidationError
from django.db import transaction
from coupons.services import validate_coupon

from products.models import Product, ProductVariant
from inventory.services import get_stock_for_product, get_stock_for_variant
from .models import Cart, CartItem


def get_or_create_cart(*, request):
    """
    Returns the cart for the current request — user cart if authenticated,
    otherwise a session-based guest cart. Ensures session exists.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
    return cart


def merge_guest_cart_into_user_cart(*, session_key, user):
    """Call this with the pre-login session key, BEFORE auth_login() rotates it."""
    if not session_key:
        return

    guest_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
    if not guest_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for guest_item in guest_cart.items.all():
        existing_item = user_cart.items.filter(
            product=guest_item.product, variant=guest_item.variant
        ).first()
        if existing_item:
            existing_item.quantity += guest_item.quantity
            existing_item.save(update_fields=["quantity"])
        else:
            guest_item.cart = user_cart
            guest_item.save(update_fields=["cart"])

    guest_cart.delete()


def _get_available_stock(*, product, variant=None):
    stock_item = get_stock_for_variant(variant=variant) if variant else get_stock_for_product(product=product)
    return stock_item.available_quantity if stock_item else 0


@transaction.atomic
def add_item_to_cart(*, cart, product_id, variant_id=None, quantity=1):
    product = Product.objects.get(pk=product_id, status="published")
    variant = None
    if variant_id:
        variant = ProductVariant.objects.get(pk=variant_id, product=product, is_active=True)

    existing_item = cart.items.filter(product=product, variant=variant).first()
    new_quantity = (existing_item.quantity + quantity) if existing_item else quantity

    available = _get_available_stock(product=product, variant=variant)
    if new_quantity > available:
        raise ValidationError(f"Only {available} item(s) available in stock.")

    if existing_item:
        existing_item.quantity = new_quantity
        existing_item.save(update_fields=["quantity", "updated_at"])
        return existing_item

    return CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=new_quantity)


@transaction.atomic
def update_cart_item_quantity(*, cart_item, quantity):
    available = _get_available_stock(product=cart_item.product, variant=cart_item.variant)
    if quantity > available:
        raise ValidationError(f"Only {available} item(s) available in stock.")

    cart_item.quantity = quantity
    cart_item.save(update_fields=["quantity", "updated_at"])
    return cart_item


def remove_cart_item(*, cart_item):
    cart_item.delete()


def clear_cart(*, cart):
    cart.items.all().delete()


def validate_cart_stock(*, cart):
    """
    Re-checks stock for every item — call this at checkout entry point,
    since items may sit in cart for a while before purchase.
    Returns a list of (cart_item, available_quantity) for items that no longer have enough stock.
    """
    problems = []
    for item in cart.items.select_related("product", "variant"):
        available = _get_available_stock(product=item.product, variant=item.variant)
        if item.quantity > available:
            problems.append((item, available))
    return problems





def get_cart_summary(*, cart, session=None, user=None):
    items = cart.items.select_related("product", "variant").prefetch_related("product__images")
    subtotal = cart.subtotal

    discount_amount = 0
    coupon = None
    coupon_code = session.get("coupon_code") if session else None

    if coupon_code:
        try:
            coupon, discount_amount = validate_coupon(code=coupon_code, subtotal=subtotal, user=user)
        except ValidationError:
            # coupon became invalid (expired, exhausted, min value no longer met, per-user limit hit) — drop it silently
            if session:
                session.pop("coupon_code", None)
            coupon = None
            discount_amount = 0

    return {
        "items": items,
        "total_items": cart.total_items,
        "subtotal": subtotal,
        "coupon": coupon,
        "discount_amount": discount_amount,
        "total": subtotal - discount_amount,
    }