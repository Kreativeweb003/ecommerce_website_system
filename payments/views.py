from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from core.permissions import superuser_required
from django.contrib import messages
from orders.services import can_access_order
from django.http import Http404

from orders.models import Order
from . import services


def payment_initiate_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, status="pending")
    if not can_access_order(request=request, order=order):
        raise Http404

    try:
        _, redirect_url = services.initiate_payment(order=order)
    except ValidationError as e:
        messages.error(request, str(e.message if hasattr(e, "message") else e))
        return redirect("payments:payment_status", order_number=order.order_number)

    return redirect(redirect_url)  # straight to the gateway's hosted page


def payment_status_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not can_access_order(request=request, order=order):
        raise Http404

    payment_transaction = services.get_transaction_for_order(order=order)
    can_retry = order.status == "pending" and (
        payment_transaction is None or payment_transaction.status in ("failed", "cancelled")
    )

    return render(request, "payments/payment_status.html", {
        "order": order,
        "transaction": payment_transaction,
        "can_retry": can_retry,
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


