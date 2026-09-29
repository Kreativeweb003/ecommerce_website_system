from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail_view, name="cart_detail"),
    path("add/", views.add_to_cart_view, name="add_to_cart"),
    path("item/<int:pk>/update/", views.update_cart_item_view, name="update_cart_item"),
    path("item/<int:pk>/remove/", views.remove_cart_item_view, name="remove_cart_item"),
    path("clear/", views.clear_cart_view, name="clear_cart"),
]
