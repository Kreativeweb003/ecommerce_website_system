import re
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    pattern = r"^\+?[0-9\s\-\(\)]{7,20}$"
    if not re.match(pattern, value):
        raise ValidationError("Enter a valid phone number.")


def validate_positive_decimal(value):
    if value is not None and value < 0:
        raise ValidationError("This value cannot be negative.")


def validate_sku_format(value):
    """SKUs across products/variants should be uppercase alphanumeric with optional hyphens."""
    pattern = r"^[A-Z0-9]+(-[A-Z0-9]+)*$"
    if not re.match(pattern, value):
        raise ValidationError("SKU must be uppercase letters/numbers, optionally separated by hyphens (e.g. SHIRT-BLU-L).")


def validate_image_file_size(image, max_size_mb=5):
    max_size_bytes = max_size_mb * 1024 * 1024
    if image.size > max_size_bytes:
        raise ValidationError(f"Image file too large. Maximum size is {max_size_mb}MB.")


def validate_future_date(value):
    from django.utils import timezone
    if value <= timezone.now():
        raise ValidationError("This date must be in the future.")




