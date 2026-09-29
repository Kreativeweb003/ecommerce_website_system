from django.urls import path
from . import views

app_name = "wishlist"

urlpatterns = [
    path("", views.wishlist_detail_view, name="wishlist_detail"),
    path("add/", views.wishlist_add_view, name="wishlist_add"),
    path("<int:item_id>/remove/", views.wishlist_remove_view, name="wishlist_remove"),
    path("<int:item_id>/move-to-cart/", views.wishlist_move_to_cart_view, name="wishlist_move_to_cart"),
]


