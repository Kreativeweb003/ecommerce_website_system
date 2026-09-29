from django import forms
from .models import ShippingZone, ShippingMethod


class ShippingZoneForm(forms.ModelForm):
    countries_raw = forms.CharField(
        widget=forms.Textarea,
        help_text="Comma-separated country codes/names, e.g. US, CA, GB",
        label="Countries",
    )

    class Meta:
        model = ShippingZone
        fields = ["name", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["countries_raw"].initial = ", ".join(self.instance.countries)

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data["countries_raw"]
        instance.countries = [c.strip() for c in raw.split(",") if c.strip()]
        if commit:
            instance.save()
        return instance


class ShippingMethodForm(forms.ModelForm):
    class Meta:
        model = ShippingMethod
        fields = [
            "zone", "name", "description", "rate_type", "flat_rate", "rate_per_kg",
            "base_rate", "free_shipping_threshold", "estimated_days_min",
            "estimated_days_max", "is_active", "display_order",
        ]


class SelectShippingMethodForm(forms.Form):
    shipping_method = forms.ModelChoiceField(queryset=ShippingMethod.objects.none(), empty_label=None)

    def __init__(self, *args, country=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .services import get_available_methods_for_country
        self.fields["shipping_method"].queryset = get_available_methods_for_country(country=country) if country else ShippingMethod.objects.none()




