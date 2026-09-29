from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home_view, name="home"),
    path("sales/", views.dashboard_sales_view, name="sales"),
    path("inventory/", views.dashboard_inventory_view, name="inventory"),
    path("payments/", views.dashboard_payments_view, name="payments"),
    path("customers/", views.dashboard_customers_view, name="customers"),
]
