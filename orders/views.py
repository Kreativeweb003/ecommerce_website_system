from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from core.permissions import superuser_required
from django.http import Http404

from cart.services import get_or_create_cart, get_cart_summary, validate_cart_stock
from . import services
from .forms import CheckoutForm, OrderStatusUpdateForm, OrderCancelForm
from .models import Order
from shipping.services import get_available_methods_for_country, get_cart_total_weight, get_cheapest_method_for_country
from django_ratelimit.decorators import ratelimit
from core.ratelimit import real_ip_key



@ratelimit(key=real_ip_key, rate="10/m", method="POST", block=True)
def checkout_view(request):
    cart = get_or_create_cart(request=request)
    summary = get_cart_summary(
        cart=cart,
        session=request.session,
        user=request.user if request.user.is_authenticated else None,
    )

    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    stock_problems = validate_cart_stock(cart=cart)
    if stock_problems:
        for item, available in stock_problems:
            messages.error(request, f"{item.display_item} only has {available} unit(s) left.")
        return redirect("cart:cart_detail")

    initial = {"coupon_code": request.session.get("coupon_code", "")}
    if request.user.is_authenticated:
        initial.update({"email": request.user.email, "phone_number": request.user.phone_number})

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = services.create_order_from_cart(
                    cart=cart,
                    checkout_data=form.cleaned_data,
                    user=request.user if request.user.is_authenticated else None,
                )
                services.remember_guest_order(request=request, order=order)
                request.session.pop("coupon_code", None)
                return redirect("payments:payment_initiate", order_number=order.order_number)
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, "message") else e))
    else:
        form = CheckoutForm(initial=initial)

    return render(request, "orders/checkout.html", {
        "form": form,
        "items": summary["items"],
        "subtotal": summary["subtotal"],
        "discount_amount": summary["discount_amount"],
        "total": summary["total"],
        # shipping options are fetched live via JS calling shipping:get_shipping_options as the
        # user types their country — no need to preload here unless doing server-rendered fallback
    })

  

def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not services.can_access_order(request=request, order=order):
        raise Http404
    return render(request, "orders/order_confirmation.html", {"order": order})



@login_required
def order_list_view(request):
    orders = services.get_orders_for_user(user=request.user)
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "status_history"),
        order_number=order_number, user=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def order_cancel_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if not order.can_be_cancelled:
        messages.error(request, "This order can no longer be cancelled.")
        return redirect("orders:order_detail", order_number=order.order_number)

    if request.method == "POST":
        form = OrderCancelForm(request.POST)
        if form.is_valid():
            services.cancel_order(order=order, reason=form.cleaned_data["reason"], user=request.user)
            messages.success(request, "Order cancelled successfully.")
            return redirect("orders:order_detail", order_number=order.order_number)
    else:
        form = OrderCancelForm()

    return render(request, "orders/order_cancel.html", {"form": form, "order": order})


# --- Admin/seller management views ---

@login_required
@superuser_required
def admin_order_list_view(request):
    status = request.GET.get("status")
    orders = services.get_all_orders(status=status)
    return render(request, "orders/admin_order_list.html", {"orders": orders, "status": status})


@login_required
@superuser_required
def admin_order_detail_view(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "status_history"), order_number=order_number
    )

    if request.method == "POST":
        form = OrderStatusUpdateForm(request.POST)
        if form.is_valid():
            try:
                services.update_order_status(
                    order=order,
                    new_status=form.cleaned_data["status"],
                    note=form.cleaned_data["note"],
                    user=request.user,
                )
                messages.success(request, "Order status updated.")
                return redirect("orders:admin_order_detail", order_number=order.order_number)
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, "message") else e))
    else:
        form = OrderStatusUpdateForm()

    return render(request, "orders/admin_order_detail.html", {"order": order, "form": form})