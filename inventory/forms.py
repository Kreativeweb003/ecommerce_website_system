from django import forms
from .models import Warehouse, StockItem


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "location", "is_active", "is_default"]


class StockAdjustmentForm(forms.Form):
    MOVEMENT_CHOICES = (
        ("purchase", "Purchase / Restock"),
        ("adjustment", "Manual Adjustment"),
        ("damage", "Damaged / Written Off"),
    )

    movement_type = forms.ChoiceField(choices=MOVEMENT_CHOICES)
    quantity_change = forms.IntegerField(help_text="Use negative numbers to remove stock.")
    reference = forms.CharField(max_length=100, required=False)
    note = forms.CharField(widget=forms.Textarea, required=False)


class StockItemThresholdForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ["low_stock_threshold"]





