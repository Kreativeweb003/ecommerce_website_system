def site_context(request):
    from cart.models import Cart
    from cart.services import get_or_create_cart
    from wishlist.services import get_or_create_wishlist

    context = {"SITE_NAME": "Northfield", "cart_item_count": 0, "wishlist_item_count": 0}

    if request.user.is_authenticated:
        context["cart_item_count"] = get_or_create_cart(request=request).total_items
        context["wishlist_item_count"] = get_or_create_wishlist(user=request.user).total_items
    elif request.session.session_key:
        guest_cart = Cart.objects.filter(session_key=request.session.session_key, user__isnull=True).first()
        if guest_cart:
            context["cart_item_count"] = guest_cart.total_items

    return context