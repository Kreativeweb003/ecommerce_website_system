from django import forms
from .models import Product, ProductImage, Category, Brand, ProductVariant


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "category", "brand", "description", "short_description",
            "base_price", "discount_price", "sku", "status", "has_variants",
            "weight_kg", "is_featured",
        ]


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "is_primary", "display_order"]


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["sku", "price_override", "image", "is_active", "attribute_values"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "parent", "description", "image", "is_active"]


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ["name", "logo", "is_active"]


class ProductFilterForm(forms.Form):
    q = forms.CharField(required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True), required=False)
    brand = forms.ModelChoiceField(queryset=Brand.objects.filter(is_active=True), required=False)
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    sort = forms.ChoiceField(
        required=False,
        choices=(
            ("newest", "Newest"),
            ("price_asc", "Price: Low to High"),
            ("price_desc", "Price: High to Low"),
            ("name", "Name A-Z"),
        ),
    )






