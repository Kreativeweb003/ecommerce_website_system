from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncDate
from orders.models import Order
from products.models import Product
from inventory.models import StockItem
from payments.models import PaymentTransaction, Refund
from reviews.models import Review
from coupons.models import Coupon
from django.core.cache import cache

CACHE_TTL_SECONDS = 300  # 5 minutes


def get_date_range(*, period="30d"):
    now = timezone.now()
    ranges = {
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "90d": now - timedelta(days=90),
        "1y": now - timedelta(days=365),
    }
    return ranges.get(period, ranges["30d"]), now


def get_sales_summary(*, period="30d"):
    start, end = get_date_range(period=period)
    paid_orders = Order.objects.filter(created_at__range=(start, end)).exclude(status__in=["pending", "cancelled"])

    summary = paid_orders.aggregate(
        total_revenue=Sum("total"),
        total_orders=Count("id"),
        average_order_value=Avg("total"),
    )

    return {
        "total_revenue": summary["total_revenue"] or 0,
        "total_orders": summary["total_orders"] or 0,
        "average_order_value": round(summary["average_order_value"], 2) if summary["average_order_value"] else 0,
        "period": period,
    }




def get_revenue_over_time(*, period="30d"):
    start, end = get_date_range(period=period)
    paid_orders = Order.objects.filter(
        created_at__range=(start, end)
    ).exclude(status__in=["pending", "cancelled"])

    daily_totals = (
        paid_orders
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("total"), order_count=Count("id"))
        .order_by("day")
    )
    return list(daily_totals)





def get_order_status_breakdown():
    return (
        Order.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )


def get_recent_orders(*, limit=10):
    return Order.objects.select_related("user").order_by("-created_at")[:limit]


def get_top_selling_products(*, period="30d", limit=10):
    from orders.models import OrderItem
    start, end = get_date_range(period=period)

    return (
        OrderItem.objects.filter(
            order__created_at__range=(start, end),
            order__status__in=["paid", "processing", "shipped", "delivered"],
        )
        .values("product__id", "product__name")
        .annotate(total_quantity_sold=Sum("quantity"), total_revenue=Sum("line_total"))
        .order_by("-total_quantity_sold")[:limit]
    )


def get_low_stock_summary(*, limit=10):
    from inventory.services import get_low_stock_items
    items = get_low_stock_items()
    return items[:limit], len(items)


def get_out_of_stock_products():
    return StockItem.objects.filter(quantity__lte=F("reserved_quantity")).select_related("product", "variant")


def get_pending_reviews_count():
    return Review.objects.filter(status="pending").count()


def get_recent_pending_reviews(*, limit=5):
    return Review.objects.filter(status="pending").select_related("product", "user").order_by("-created_at")[:limit]


def get_active_coupons_summary():
    active_coupons = Coupon.objects.filter(is_active=True)
    return {
        "total_active": active_coupons.count(),
        "total_redemptions": active_coupons.aggregate(total=Sum("times_used"))["total"] or 0,
        "expiring_soon": active_coupons.filter(
            valid_until__isnull=False,
            valid_until__lte=timezone.now() + timedelta(days=7),
            valid_until__gte=timezone.now(),
        ),
    }


def get_payment_summary(*, period="30d"):
    start, end = get_date_range(period=period)
    transactions = PaymentTransaction.objects.filter(created_at__range=(start, end))

    return {
        "succeeded": transactions.filter(status="succeeded").count(),
        "failed": transactions.filter(status="failed").count(),
        "pending": transactions.filter(status="pending").count(),
        "total_refunded": Refund.objects.filter(
            status="succeeded", created_at__range=(start, end)
        ).aggregate(total=Sum("amount"))["total"] or 0,
    }


def get_customer_summary(*, period="30d"):
    from accounts.models import User
    start, end = get_date_range(period=period)

    new_customers = User.objects.filter(date_joined__range=(start, end), is_staff=False).count()

    repeat_customer_ids = (
        Order.objects.exclude(status__in=["pending", "cancelled"])
        .values("user")
        .annotate(order_count=Count("id"))
        .filter(order_count__gt=1, user__isnull=False)
    )

    return {
        "new_customers": new_customers,
        "repeat_customers": repeat_customer_ids.count(),
    }





def get_dashboard_overview(*, period="30d"):
    cache_key = f"dashboard:overview:{period}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    low_stock_items, low_stock_count = get_low_stock_summary()

    overview = {
        "sales_summary": get_sales_summary(period=period),
        "revenue_over_time": get_revenue_over_time(period=period),
        "order_status_breakdown": list(get_order_status_breakdown()),
        "recent_orders": list(get_recent_orders()),
        "top_selling_products": list(get_top_selling_products(period=period)),
        "low_stock_items": low_stock_items,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": get_out_of_stock_products().count(),
        "pending_reviews_count": get_pending_reviews_count(),
        "recent_pending_reviews": list(get_recent_pending_reviews()),
        "coupon_summary": get_active_coupons_summary(),
        "payment_summary": get_payment_summary(period=period),
        "customer_summary": get_customer_summary(period=period),
    }

    cache.set(cache_key, overview, CACHE_TTL_SECONDS)
    return overview

