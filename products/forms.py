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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            excluded_ids = {self.instance.pk} | self._descendant_ids(self.instance)
            self.fields["parent"].queryset = Category.objects.exclude(pk__in=excluded_ids)

    @staticmethod
    def _descendant_ids(category):
        ids = set()
        to_visit = list(category.subcategories.values_list("pk", flat=True))
        while to_visit:
            pk = to_visit.pop()
            if pk in ids:
                continue
            ids.add(pk)
            to_visit.extend(Category.objects.filter(parent_id=pk).values_list("pk", flat=True))
        return ids
    
    def clean_image(self):
        image = self.cleaned_data.get("image")
        # Only freshly uploaded files have a content_type; an already-saved image is skipped.
        if image and hasattr(image, "content_type"):
            from .services import validate_image_file
            validate_image_file(image)
        return image




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






