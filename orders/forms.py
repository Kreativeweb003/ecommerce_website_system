from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)

    shipping_full_name = forms.CharField(max_length=150)
    shipping_street_address = forms.CharField(max_length=255)
    shipping_apartment = forms.CharField(max_length=100, required=False)
    shipping_city = forms.CharField(max_length=100)
    shipping_state = forms.CharField(max_length=100)
    shipping_postal_code = forms.CharField(max_length=20)
    shipping_country = forms.CharField(max_length=100)

    shipping_method_id = forms.IntegerField(widget=forms.HiddenInput)

    billing_same_as_shipping = forms.BooleanField(required=False, initial=True)
    billing_full_name = forms.CharField(max_length=150, required=False)
    billing_street_address = forms.CharField(max_length=255, required=False)
    billing_apartment = forms.CharField(max_length=100, required=False)
    billing_city = forms.CharField(max_length=100, required=False)
    billing_state = forms.CharField(max_length=100, required=False)
    billing_postal_code = forms.CharField(max_length=20, required=False)
    billing_country = forms.CharField(max_length=100, required=False)

    coupon_code = forms.CharField(max_length=50, required=False)
    customer_note = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("billing_same_as_shipping"):
            required_billing_fields = [
                "billing_full_name", "billing_street_address", "billing_city",
                "billing_state", "billing_postal_code", "billing_country",
            ]
            for field in required_billing_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "This field is required when billing differs from shipping.")
        return cleaned_data

class OrderStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=[
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ])
    note = forms.CharField(widget=forms.Textarea, required=False)


class OrderCancelForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, required=False)