from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("products/", views.product_list_view, name="product_list"),
    path("products/create/", views.product_create_view, name="product_create"),
    path("products/<slug:slug>/", views.product_detail_view, name="product_detail"),
    path("products/<slug:slug>/edit/", views.product_update_view, name="product_update"),
    path("products/<slug:slug>/delete/", views.product_delete_view, name="product_delete"),
    path("products/<slug:slug>/variants/add/", views.variant_create_view, name="variant_create"),
    path("category/<slug:slug>/", views.category_view, name="category_detail"),
    path("manage/products/", views.admin_product_list_view, name="admin_product_list"),
]