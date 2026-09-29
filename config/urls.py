from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("products.urls")),
    path("accounts/", include("accounts.urls")),
    path("inventory/", include("inventory.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("coupons/", include("coupons.urls")),
    path("payments/", include("payments.urls")),
    path("shipping/", include("shipping.urls")),
    path("reviews/", include("reviews.urls")),
    path("wishlist/", include("wishlist.urls")),
    path("dashboard/", include("dashboard.urls")),
]
