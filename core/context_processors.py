def site_context(request):
    """
    Injected into every template via settings.TEMPLATES — avoids every view having to
    manually pass cart totals, wishlist counts, etc. into context.
    """
    context = {
        "SITE_NAME": "Your Store",
    }

    if request.user.is_authenticated:
        from cart.services import get_or_create_cart
        from wishlist.services import get_or_create_wishlist

        cart = get_or_create_cart(request=request)
        wishlist = get_or_create_wishlist(user=request.user)

        context["cart_item_count"] = cart.total_items
        context["wishlist_item_count"] = wishlist.total_items
    else:
        context["cart_item_count"] = 0
        context["wishlist_item_count"] = 0

    return context


