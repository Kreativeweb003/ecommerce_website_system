from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from core.permissions import superuser_required

from . import services
from .models import Warehouse, StockItem
from .forms import WarehouseForm, StockAdjustmentForm, StockItemThresholdForm


@login_required
@superuser_required
def stock_dashboard_view(request):
    warehouses = Warehouse.objects.filter(is_active=True)
    selected_warehouse_id = request.GET.get("warehouse")
    warehouse = warehouses.filter(pk=selected_warehouse_id).first() if selected_warehouse_id else None

    stock_items = StockItem.objects.select_related("product", "variant", "warehouse")
    if warehouse:
        stock_items = stock_items.filter(warehouse=warehouse)

    low_stock_items = services.get_low_stock_items(warehouse=warehouse)

    return render(request, "inventory/dashboard.html", {
        "warehouses": warehouses,
        "selected_warehouse": warehouse,
        "stock_items": stock_items,
        "low_stock_items": low_stock_items,
    })


@login_required
@superuser_required
def stock_adjust_view(request, pk):
    stock_item = get_object_or_404(StockItem, pk=pk)

    if request.method == "POST":
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                services.adjust_stock(
                    stock_item=stock_item,
                    quantity_change=form.cleaned_data["quantity_change"],
                    movement_type=form.cleaned_data["movement_type"],
                    reference=form.cleaned_data["reference"],
                    note=form.cleaned_data["note"],
                    user=request.user,
                )
                messages.success(request, "Stock adjusted successfully.")
                return redirect("inventory:stock_dashboard")
            except ValidationError as e:
                form.add_error(None, e.message)
    else:
        form = StockAdjustmentForm()

    return render(request, "inventory/stock_adjust.html", {"form": form, "stock_item": stock_item})


@login_required
@superuser_required
def stock_threshold_view(request, pk):
    stock_item = get_object_or_404(StockItem, pk=pk)

    if request.method == "POST":
        form = StockItemThresholdForm(request.POST, instance=stock_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Low stock threshold updated.")
            return redirect("inventory:stock_dashboard")
    else:
        form = StockItemThresholdForm(instance=stock_item)

    return render(request, "inventory/stock_threshold.html", {"form": form, "stock_item": stock_item})


@login_required
@superuser_required
def stock_movement_history_view(request, pk):
    stock_item = get_object_or_404(StockItem, pk=pk)
    movements = services.get_movement_history(stock_item=stock_item)

    return render(request, "inventory/movement_history.html", {
        "stock_item": stock_item,
        "movements": movements,
    })


@login_required
@superuser_required
def warehouse_list_view(request):
    warehouses = Warehouse.objects.all()
    return render(request, "inventory/warehouse_list.html", {"warehouses": warehouses})


@login_required
@superuser_required
def warehouse_create_view(request):
    if request.method == "POST":
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Warehouse created successfully.")
            return redirect("inventory:warehouse_list")
    else:
        form = WarehouseForm()

    return render(request, "inventory/warehouse_form.html", {"form": form, "action": "Create"})


@login_required
@superuser_required
def warehouse_update_view(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == "POST":
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(request, "Warehouse updated successfully.")
            return redirect("inventory:warehouse_list")
    else:
        form = WarehouseForm(instance=warehouse)

    return render(request, "inventory/warehouse_form.html", {"form": form, "action": "Edit"})





