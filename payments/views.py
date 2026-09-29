from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from core.permissions import superuser_required

from orders.models import Order
from . import services


@login_required
@superuser_required
def payment_initiate_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user, status="pending")

    payment_transaction, redirect_or_secret = services.initiate_payment(order=order)

    return render(request, "payments/payment_checkout.html", {
        "order": order,
        "transaction": payment_transaction,
        "client_secret_or_redirect_url": redirect_or_secret,
    })


def payment_status_view(request, order_number):
    """Polled or landed on after redirect back from gateway-hosted payment pages (e.g. Paystack)."""
    order = get_object_or_404(Order, order_number=order_number)
    payment_transaction = services.get_transaction_for_order(order=order)

    return render(request, "payments/payment_status.html", {
        "order": order,
        "transaction": payment_transaction,
    })


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    try:
        services.process_webhook_event(
            gateway_name="stripe", payload_body=request.body, headers=request.headers,
        )
        return HttpResponse(status=200)
    except ValidationError as e:
        return HttpResponse(str(e), status=400)


@csrf_exempt
@require_POST
def paystack_webhook_view(request):
    try:
        services.process_webhook_event(
            gateway_name="paystack", payload_body=request.body, headers=request.headers,
        )
        return HttpResponse(status=200)
    except ValidationError as e:
        return HttpResponse(str(e), status=400)


@login_required
def refund_initiate_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == "POST":
        try:
            services.initiate_refund(order=order, reason=request.POST.get("reason", ""), user=request.user)
            return JsonResponse({"success": True})
        except ValidationError as e:
            return JsonResponse({"success": False, "error": str(e.message if hasattr(e, "message") else e)}, status=400)

    return render(request, "payments/refund_form.html", {"order": order})


