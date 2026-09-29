from django.urls import path
from . import views

app_name = "shipping"

urlpatterns = [
    path("options/", views.get_shipping_options_view, name="get_shipping_options"),

    path("manage/zones/", views.zone_list_view, name="zone_list"),
    path("manage/zones/create/", views.zone_create_view, name="zone_create"),
    path("manage/zones/<int:pk>/edit/", views.zone_update_view, name="zone_update"),

    path("manage/methods/create/", views.method_create_view, name="method_create"),
    path("manage/methods/<int:pk>/edit/", views.method_update_view, name="method_update"),
]
