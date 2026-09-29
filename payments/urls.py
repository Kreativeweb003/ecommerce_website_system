from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("pay/<str:order_number>/", views.payment_initiate_view, name="payment_initiate"),
    path("status/<str:order_number>/", views.payment_status_view, name="payment_status"),

    path("webhooks/stripe/", views.stripe_webhook_view, name="stripe_webhook"),
    path("webhooks/paystack/", views.paystack_webhook_view, name="paystack_webhook"),

    path("refund/<str:order_number>/", views.refund_initiate_view, name="refund_initiate"),
]
