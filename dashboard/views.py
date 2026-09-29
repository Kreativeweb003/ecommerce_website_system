from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from core.permissions import superuser_required
from . import services


@login_required
@superuser_required
def dashboard_home_view(request):
    period = request.GET.get("period", "30d")
    if period not in ("7d", "30d", "90d", "1y"):
        period = "30d"

    overview = services.get_dashboard_overview(period=period)

    return render(request, "dashboard/home.html", {
        "period": period,
        **overview,
    })


@login_required
@superuser_required
def dashboard_sales_view(request):
    period = request.GET.get("period", "30d")
    if period not in ("7d", "30d", "90d", "1y"):
        period = "30d"

    return render(request, "dashboard/sales.html", {
        "period": period,
        "sales_summary": services.get_sales_summary(period=period),
        "revenue_over_time": services.get_revenue_over_time(period=period),
        "order_status_breakdown": services.get_order_status_breakdown(),
        "top_selling_products": services.get_top_selling_products(period=period, limit=20),
    })


@login_required
@superuser_required
def dashboard_inventory_view(request):
    low_stock_items, low_stock_count = services.get_low_stock_summary(limit=50)
    out_of_stock = services.get_out_of_stock_products()

    return render(request, "dashboard/inventory.html", {
        "low_stock_items": low_stock_items,
        "low_stock_count": low_stock_count,
        "out_of_stock_products": out_of_stock,
    })


@login_required
@superuser_required
def dashboard_payments_view(request):
    period = request.GET.get("period", "30d")
    if period not in ("7d", "30d", "90d", "1y"):
        period = "30d"

    return render(request, "dashboard/payments.html", {
        "period": period,
        "payment_summary": services.get_payment_summary(period=period),
    })


@login_required
@superuser_required
def dashboard_customers_view(request):
    period = request.GET.get("period", "30d")
    if period not in ("7d", "30d", "90d", "1y"):
        period = "30d"

    return render(request, "dashboard/customers.html", {
        "period": period,
        "customer_summary": services.get_customer_summary(period=period),
    })



