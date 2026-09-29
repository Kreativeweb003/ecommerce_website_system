from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from core.permissions import superuser_required

from core.utils import is_ajax
from cart.services import get_or_create_cart
from . import services
from .forms import ApplyCouponForm, CouponForm
from .models import Coupon
from django_ratelimit.decorators import ratelimit
from core.ratelimit import real_ip_key




@ratelimit(key=real_ip_key, rate="10/m", method="POST", block=True)
def apply_coupon_view(request):
    if request.method == "POST":
        form = ApplyCouponForm(request.POST)
        if form.is_valid():
            cart = get_or_create_cart(request=request)
            try:
                coupon, discount = services.validate_coupon(
                    code=form.cleaned_data["code"],
                    subtotal=cart.subtotal,
                    user=request.user if request.user.is_authenticated else None,
                )
                request.session["coupon_code"] = coupon.code

                if is_ajax(request):
                    summary = get_cart_summary(
                        cart=cart, session=request.session,
                        user=request.user if request.user.is_authenticated else None,
                    )
                    return JsonResponse({
                        "success": True,
                        "coupon_code": coupon.code,
                        "discount_amount": str(summary["discount_amount"]),
                        "total": str(summary["total"]),
                    })
                messages.success(request, f"Coupon '{coupon.code}' applied — you saved {discount}.")
            except ValidationError as e:
                request.session.pop("coupon_code", None)
                error_message = str(e.message if hasattr(e, "message") else e)
                if is_ajax(request):
                    return JsonResponse({"success": False, "error": error_message}, status=400)
                messages.error(request, error_message)
        elif is_ajax(request):
            return JsonResponse({"success": False, "error": "Enter a coupon code."}, status=400)

    return redirect("cart:cart_detail")


def remove_coupon_view(request):
    request.session.pop("coupon_code", None)

    if is_ajax(request):
        cart = get_or_create_cart(request=request)
        summary = get_cart_summary(
            cart=cart, session=request.session,
            user=request.user if request.user.is_authenticated else None,
        )
        return JsonResponse({"success": True, "subtotal": str(summary["subtotal"]), "total": str(summary["total"])})

    messages.info(request, "Coupon removed.")
    return redirect("cart:cart_detail")



@login_required
@superuser_required
def coupon_list_view(request):
    coupons = Coupon.objects.all()
    return render(request, "coupons/coupon_list.html", {"coupons": coupons})


@login_required
@superuser_required
def coupon_create_view(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon created successfully.")
            return redirect("coupons:coupon_list")
    else:
        form = CouponForm()

    return render(request, "coupons/coupon_form.html", {"form": form, "action": "Create"})


@login_required
@superuser_required
def coupon_update_view(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)

    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully.")
            return redirect("coupons:coupon_list")
    else:
        form = CouponForm(instance=coupon)

    return render(request, "coupons/coupon_form.html", {"form": form, "action": "Edit"})