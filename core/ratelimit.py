from .utils import get_client_ip


def real_ip_key(group, request):
    """
    Custom key function for django-ratelimit — resolves the real client IP
    behind a reverse proxy instead of trusting REMOTE_ADDR directly.
    Pass this as key=real_ip_key on any @ratelimit decorator.
    """
    return get_client_ip(request)