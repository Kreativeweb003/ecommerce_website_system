from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from core.utils import is_ajax
from . import services
from .forms import AddToCartForm, UpdateCartItemForm
from .models import CartItem


def cart_detail_view(request):
    cart = services.get_or_create_cart(request=request)
    summary = services.get_cart_summary(
        cart=cart, session=request.session,
        user=request.user if request.user.is_authenticated else None,
    )

    return render(request, "cart/cart_detail.html", {
        "cart": cart,
        "items": summary["items"],
        "total_items": summary["total_items"],
        "subtotal": summary["subtotal"],
        "coupon": summary["coupon"],
        "discount_amount": summary["discount_amount"],
        "total": summary["total"],
    })


def _cart_summary_json(*, cart, request):
    """Shared shape for every cart AJAX response, so the frontend has one consistent contract."""
    summary = services.get_cart_summary(
        cart=cart, session=request.session,
        user=request.user if request.user.is_authenticated else None,
    )
    return {
        "total_items": summary["total_items"],
        "subtotal": str(summary["subtotal"]),
        "discount_amount": str(summary["discount_amount"]),
        "total": str(summary["total"]),
        "coupon_code": summary["coupon"].code if summary["coupon"] else None,
    }


@require_POST
def add_to_cart_view(request):
    form = AddToCartForm(request.POST)
    if form.is_valid():
        cart = services.get_or_create_cart(request=request)
        try:
            services.add_item_to_cart(
                cart=cart,
                product_id=form.cleaned_data["product_id"],
                variant_id=form.cleaned_data.get("variant_id"),
                quantity=form.cleaned_data["quantity"],
            )
            if is_ajax(request):
                return JsonResponse({"success": True, **_cart_summary_json(cart=cart, request=request)})
            messages.success(request, "Item added to cart.")
        except ValidationError as e:
            error_message = str(e.message if hasattr(e, "message") else e)
            if is_ajax(request):
                return JsonResponse({"success": False, "error": error_message}, status=400)
            messages.error(request, error_message)
    else:
        if is_ajax(request):
            return JsonResponse({"success": False, "error": "Invalid request."}, status=400)
        messages.error(request, "Could not add item to cart.")

    next_url = request.POST.get("next", "cart:cart_detail")
    return redirect(next_url)


@require_POST
def update_cart_item_view(request, pk):
    cart = services.get_or_create_cart(request=request)
    cart_item = get_object_or_404(CartItem, pk=pk, cart=cart)

    form = UpdateCartItemForm(request.POST)
    if form.is_valid():
        try:
            services.update_cart_item_quantity(cart_item=cart_item, quantity=form.cleaned_data["quantity"])
            if is_ajax(request):
                return JsonResponse({
                    "success": True,
                    "item_id": cart_item.pk,
                    "line_total": str(cart_item.total_price),
                    **_cart_summary_json(cart=cart, request=request),
                })
            messages.success(request, "Cart updated.")
        except ValidationError as e:
            error_message = str(e.message if hasattr(e, "message") else e)
            if is_ajax(request):
                return JsonResponse({"success": False, "error": error_message}, status=400)
            messages.error(request, error_message)
    elif is_ajax(request):
        return JsonResponse({"success": False, "error": "Invalid quantity."}, status=400)

    return redirect("cart:cart_detail")


@require_POST
def remove_cart_item_view(request, pk):
    cart = services.get_or_create_cart(request=request)
    cart_item = get_object_or_404(CartItem, pk=pk, cart=cart)
    services.remove_cart_item(cart_item=cart_item)

    if is_ajax(request):
        return JsonResponse({"success": True, "item_id": pk, **_cart_summary_json(cart=cart, request=request)})

    messages.info(request, "Item removed from cart.")
    return redirect("cart:cart_detail")


@require_POST
def clear_cart_view(request):
    cart = services.get_or_create_cart(request=request)
    services.clear_cart(cart=cart)

    if is_ajax(request):
        return JsonResponse({"success": True, **_cart_summary_json(cart=cart, request=request)})

    messages.info(request, "Cart cleared.")
    return redirect("cart:cart_detail")

