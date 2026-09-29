from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

from notifications.services import notify_wishlist_price_drop, notify_wishlist_back_in_stock
from .models import Wishlist, WishlistItem


def get_or_create_wishlist(*, user):
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return wishlist


def is_in_wishlist(*, user, product, variant=None):
    wishlist = get_or_create_wishlist(user=user)
    return wishlist.items.filter(product=product, variant=variant).exists()


@transaction.atomic
def add_to_wishlist(*, user, product, variant=None):
    wishlist = get_or_create_wishlist(user=user)
    price = variant.price if variant else product.current_price

    try:
        item = WishlistItem.objects.create(
            wishlist=wishlist, product=product, variant=variant, price_at_addition=price
        )
    except IntegrityError:
        raise ValidationError("This item is already in your wishlist.")

    return item


def remove_from_wishlist(*, user, item_id):
    wishlist = get_or_create_wishlist(user=user)
    item = wishlist.items.filter(pk=item_id).first()
    if not item:
        raise ValidationError("Item not found in your wishlist.")
    item.delete()


def get_wishlist_items(*, user):
    wishlist = get_or_create_wishlist(user=user)
    return wishlist.items.select_related("product", "variant").prefetch_related("product__images")


def move_to_cart(*, user, item_id, cart, quantity=1):
    """Removes from wishlist and adds to cart in one action — common UX pattern."""
    from cart.services import add_item_to_cart

    wishlist = get_or_create_wishlist(user=user)
    item = wishlist.items.filter(pk=item_id).first()
    if not item:
        raise ValidationError("Item not found in your wishlist.")

    cart_item = add_item_to_cart(
        cart=cart,
        product_id=item.product_id,
        variant_id=item.variant_id,
        quantity=quantity,
    )
    item.delete()
    return cart_item


def check_and_notify_price_drop(*, product=None, variant=None):
    """
    Call this whenever a product/variant price changes (e.g. from an admin save signal).
    Notifies every wishlisting user once per drop — resets when price goes back up.
    """
    queryset = WishlistItem.objects.filter(variant=variant) if variant else WishlistItem.objects.filter(
        product=product, variant__isnull=True
    )

    for item in queryset.select_related("wishlist__user", "product", "variant"):
        if item.has_price_dropped and not item.notified_price_drop:
            notify_wishlist_price_drop(user=item.wishlist.user, wishlist_item=item)
            item.notified_price_drop = True
            item.save(update_fields=["notified_price_drop"])
        elif not item.has_price_dropped and item.notified_price_drop:
            # price went back up (or above original) — reset so a future drop notifies again
            item.notified_price_drop = False
            item.save(update_fields=["notified_price_drop"])


def check_and_notify_back_in_stock(*, product=None, variant=None):
  
    from inventory.services import get_stock_for_product, get_stock_for_variant

    """Call this after any stock increase (restock) via inventory.adjust_stock."""
    stock_item = get_stock_for_variant(variant=variant) if variant else get_stock_for_product(product=product)
    if not stock_item or stock_item.available_quantity <= 0:
        return

    queryset = WishlistItem.objects.filter(variant=variant) if variant else WishlistItem.objects.filter(
        product=product, variant__isnull=True
    )

    for item in queryset.filter(notified_back_in_stock=False).select_related("wishlist__user", "product", "variant"):
        notify_wishlist_back_in_stock(user=item.wishlist.user, wishlist_item=item)
        item.notified_back_in_stock = True
        item.save(update_fields=["notified_back_in_stock"])



