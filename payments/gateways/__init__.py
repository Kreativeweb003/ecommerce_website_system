from django.conf import settings

from .stripe_gateway import StripeGateway
from .paystack_gateway import PaystackGateway

_GATEWAYS = {
    "stripe": StripeGateway,
    "paystack": PaystackGateway,
}


def get_gateway(name=None):
    """Returns an instantiated gateway. Defaults to settings.DEFAULT_PAYMENT_GATEWAY."""
    name = name or settings.DEFAULT_PAYMENT_GATEWAY
    gateway_class = _GATEWAYS.get(name)
    if not gateway_class:
        raise ValueError(f"Unknown payment gateway: {name}")
    return gateway_class()



