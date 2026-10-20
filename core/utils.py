import uuid
import unicodedata
import re
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings


from django.utils.http import url_has_allowed_host_and_scheme


def get_safe_redirect_url(request, default, param="next"):
    """Returns ?next= only if it points at this site; otherwise the default."""
    candidate = request.POST.get(param) or request.GET.get(param)
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return default


def generate_reference_code(*, prefix="REF", length=10):
    """Generic unique code generator — used as a pattern by orders, payments, coupons, etc."""
    return f"{prefix}-{uuid.uuid4().hex[:length].upper()}"


def slugify_unicode(value):
    """Handles non-ASCII product/category names better than Django's default slugify in edge cases."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def round_currency(value, decimal_places=2):
    """Consistent rounding for money — avoids float rounding surprises across the codebase."""
    quantize_target = Decimal("1." + ("0" * decimal_places)) if decimal_places else Decimal("1")
    return Decimal(value).quantize(quantize_target, rounding=ROUND_HALF_UP)


def get_client_ip(request):
    """
    X-Forwarded-For is client-controlled at its left end, so trust only the entry added by
    our own proxy(ies): the Nth from the right. With TRUSTED_PROXY_COUNT=0 (default) it is ignored.
    """
    proxy_count = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if proxy_count and forwarded_for:
        parts = [p.strip() for p in forwarded_for.split(",") if p.strip()]
        if len(parts) >= proxy_count:
            return parts[-proxy_count]
    return request.META.get("REMOTE_ADDR")


def mask_email(email):
    """e.g. 'john.doe@example.com' -> 'j***e@example.com' — for display in logs/admin without full exposure."""
    try:
        local, domain = email.split("@")
        if len(local) <= 2:
            masked_local = local[0] + "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"
    except ValueError:
        return email


def chunked(iterable, size):
    """Splits an iterable into fixed-size chunks — useful for bulk operations (bulk_create, etc)."""
    iterable = list(iterable)
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def is_ajax(request):
    """
    Detects fetch()-based requests. Relies on the X-Requested-With header,
    which every fetch call in our JS explicitly sets (see static/js/main.js) —
    browsers don't set this automatically like old jQuery.ajax() used to.
    """
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


