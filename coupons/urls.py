from django.urls import path
from . import views

app_name = "coupons"

urlpatterns = [
    path("apply/", views.apply_coupon_view, name="apply_coupon"),
    path("remove/", views.remove_coupon_view, name="remove_coupon"),

    path("manage/", views.coupon_list_view, name="coupon_list"),
    path("manage/create/", views.coupon_create_view, name="coupon_create"),
    path("manage/<int:pk>/edit/", views.coupon_update_view, name="coupon_update"),
]
