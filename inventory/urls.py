from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.stock_dashboard_view, name="stock_dashboard"),
    path("stock/<int:pk>/adjust/", views.stock_adjust_view, name="stock_adjust"),
    path("stock/<int:pk>/threshold/", views.stock_threshold_view, name="stock_threshold"),
    path("stock/<int:pk>/history/", views.stock_movement_history_view, name="stock_movement_history"),

    path("warehouses/", views.warehouse_list_view, name="warehouse_list"),
    path("warehouses/create/", views.warehouse_create_view, name="warehouse_create"),
    path("warehouses/<int:pk>/edit/", views.warehouse_update_view, name="warehouse_update"),
]



