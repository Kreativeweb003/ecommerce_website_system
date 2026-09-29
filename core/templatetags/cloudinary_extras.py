from django import template

register = template.Library()


@register.filter
def optimized(image_field, transformation="q_auto,f_auto"):
    """
    Usage in a template: {{ product.images.first.image|optimized }}
    Or with a custom transformation: {{ product.images.first.image|optimized:"q_auto,f_auto,w_400" }}

    Injects Cloudinary's transformation string into the delivery URL —
    q_auto = automatic quality compression, f_auto = automatic best format (WebP/AVIF where supported).
    Falls back to the plain URL if the file isn't actually a Cloudinary-backed field
    (e.g. running locally without Cloudinary configured) so templates don't break in dev.
    """
    if not image_field:
        return ""

    try:
        url = image_field.url
    except (ValueError, AttributeError):
        return ""

    if "res.cloudinary.com" not in url:
        # Not a Cloudinary URL (e.g. local dev without Cloudinary configured) — return as-is.
        return url

    # Cloudinary URLs look like: https://res.cloudinary.com/<cloud>/image/upload/v123/path.jpg
    # We inject the transformation string right after "/upload/".
    marker = "/upload/"
    if marker not in url:
        return url

    base, _, rest = url.partition(marker)
    return f"{base}{marker}{transformation}/{rest}"


@register.simple_tag
def optimized_thumbnail(image_field, width=300, height=300):
    """
    Usage: {% optimized_thumbnail product.images.first.image 150 150 %}
    Convenience wrapper for a common case — square-ish cropped thumbnail, auto quality/format.
    """
    return optimized(image_field, transformation=f"q_auto,f_auto,w_{width},h_{height},c_fill")