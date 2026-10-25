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
    path("manage/categories/", views.admin_category_list_view, name="admin_category_list"),
    path("manage/categories/create/", views.admin_category_create_view, name="admin_category_create"),
    path("manage/categories/<int:pk>/edit/", views.admin_category_update_view, name="admin_category_update"),
    path("manage/categories/<int:pk>/delete/", views.admin_category_delete_view, name="admin_category_delete"),
    path("manage/brands/", views.admin_brand_list_view, name="admin_brand_list"),
    path("manage/brands/create/", views.admin_brand_create_view, name="admin_brand_create"),
    path("manage/brands/<int:pk>/edit/", views.admin_brand_update_view, name="admin_brand_update"),
    path("manage/brands/<int:pk>/delete/", views.admin_brand_delete_view, name="admin_brand_delete"),

    path("manage/products/<slug:slug>/images/add/", views.admin_product_image_add_view, name="admin_product_image_add"),
    path("manage/images/<int:pk>/delete/", views.admin_product_image_delete_view, name="admin_product_image_delete"),
    path("manage/images/<int:pk>/primary/", views.admin_product_image_primary_view, name="admin_product_image_primary"),
    path("manage/categories/<int:pk>/image/delete/", views.admin_category_image_delete_view, name="admin_category_image_delete"),
]