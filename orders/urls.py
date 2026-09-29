from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout_view, name="checkout"),
    path("confirmation/<str:order_number>/", views.order_confirmation_view, name="order_confirmation"),

    path("my-orders/", views.order_list_view, name="order_list"),
    path("my-orders/<str:order_number>/", views.order_detail_view, name="order_detail"),
    path("my-orders/<str:order_number>/cancel/", views.order_cancel_view, name="order_cancel"),

    path("manage/", views.admin_order_list_view, name="admin_order_list"),
    path("manage/<str:order_number>/", views.admin_order_detail_view, name="admin_order_detail"),
]
