from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from core.permissions import superuser_required

from cart.services import get_or_create_cart
from . import services
from .forms import ShippingZoneForm, ShippingMethodForm
from .models import ShippingZone, ShippingMethod


def get_shipping_options_view(request):
    """
    AJAX endpoint — called from the checkout page whenever the user enters/changes
    their shipping country, to populate available methods and live costs.
    """
    country = request.GET.get("country", "")
    if not country:
        return JsonResponse({"methods": []})

    cart = get_or_create_cart(request=request)
    subtotal = cart.subtotal
    total_weight_kg = services.get_cart_total_weight(cart=cart)

    methods = services.get_available_methods_for_country(country=country)
    options = [
        {
            "id": method.id,
            "name": method.name,
            "description": method.description,
            "cost": str(method.calculate_cost(subtotal=subtotal, total_weight_kg=total_weight_kg)),
            "estimated_delivery": method.estimated_delivery_label,
        }
        for method in methods
    ]

    return JsonResponse({"methods": options})


# --- Admin management views ---

@login_required
@superuser_required
def zone_list_view(request):
    zones = ShippingZone.objects.prefetch_related("methods")
    return render(request, "shipping/zone_list.html", {"zones": zones})


@login_required
@superuser_required
def zone_create_view(request):
    if request.method == "POST":
        form = ShippingZoneForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Shipping zone created.")
            return redirect("shipping:zone_list")
    else:
        form = ShippingZoneForm()

    return render(request, "shipping/zone_form.html", {"form": form, "action": "Create"})


@login_required
@superuser_required
def zone_update_view(request, pk):
    zone = get_object_or_404(ShippingZone, pk=pk)

    if request.method == "POST":
        form = ShippingZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            messages.success(request, "Shipping zone updated.")
            return redirect("shipping:zone_list")
    else:
        form = ShippingZoneForm(instance=zone)

    return render(request, "shipping/zone_form.html", {"form": form, "action": "Edit"})


@login_required
@superuser_required
def method_create_view(request):
    if request.method == "POST":
        form = ShippingMethodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Shipping method created.")
            return redirect("shipping:zone_list")
    else:
        form = ShippingMethodForm()

    return render(request, "shipping/method_form.html", {"form": form, "action": "Create"})


@login_required
@superuser_required
def method_update_view(request, pk):
    method = get_object_or_404(ShippingMethod, pk=pk)

    if request.method == "POST":
        form = ShippingMethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, "Shipping method updated.")
            return redirect("shipping:zone_list")
    else:
        form = ShippingMethodForm(instance=method)

    return render(request, "shipping/method_form.html", {"form": form, "action": "Edit"})


