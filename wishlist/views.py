from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from core.utils import get_safe_redirect_url

from core.utils import is_ajax
from products.models import Product, ProductVariant
from cart.services import get_or_create_cart
from . import services


@login_required
def wishlist_detail_view(request):
    items = services.get_wishlist_items(user=request.user)
    return render(request, "wishlist/wishlist_detail.html", {"items": items})


@login_required
@require_POST
def wishlist_add_view(request):
    product_id = request.POST.get("product_id")
    variant_id = request.POST.get("variant_id")

    product = get_object_or_404(Product, pk=product_id)
    variant = get_object_or_404(ProductVariant, pk=variant_id) if variant_id else None

    try:
        item = services.add_to_wishlist(user=request.user, product=product, variant=variant)
        if is_ajax(request):
            return JsonResponse({"success": True, "item_id": item.pk, "message": "Added to wishlist."})
        messages.success(request, "Added to wishlist.")
    except ValidationError as e:
        error_message = str(e.message if hasattr(e, "message") else e)
        if is_ajax(request):
            return JsonResponse({"success": False, "error": error_message}, status=400)
        messages.info(request, error_message)

    return redirect(get_safe_redirect_url(request, "wishlist:wishlist_detail"))


@login_required
@require_POST
def wishlist_remove_view(request, item_id):
    try:
        services.remove_from_wishlist(user=request.user, item_id=item_id)
        if is_ajax(request):
            return JsonResponse({"success": True, "item_id": item_id})
        messages.info(request, "Removed from wishlist.")
    except ValidationError as e:
        error_message = str(e.message if hasattr(e, "message") else e)
        if is_ajax(request):
            return JsonResponse({"success": False, "error": error_message}, status=400)
        messages.error(request, error_message)

    return redirect("wishlist:wishlist_detail")


@login_required
@require_POST
def wishlist_move_to_cart_view(request, item_id):
    cart = get_or_create_cart(request=request)

    try:
        services.move_to_cart(user=request.user, item_id=item_id, cart=cart)
        if is_ajax(request):
            return JsonResponse({"success": True, "item_id": item_id, "total_items": cart.total_items})
        messages.success(request, "Moved to cart.")
        return redirect("cart:cart_detail")
    except ValidationError as e:
        error_message = str(e.message if hasattr(e, "message") else e)
        if is_ajax(request):
            return JsonResponse({"success": False, "error": error_message}, status=400)
        messages.error(request, error_message)
        return redirect("wishlist:wishlist_detail")