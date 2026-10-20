import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def expire_pending_orders():
    from .models import Order
    from .services import cancel_order

    minutes = getattr(settings, "PENDING_ORDER_EXPIRY_MINUTES", 60)
    cutoff = timezone.now() - timedelta(minutes=minutes)
    stale_ids = list(
        Order.objects.filter(status="pending", created_at__lt=cutoff).values_list("pk", flat=True)
    )

    cancelled = 0
    for pk in stale_ids:
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=pk)
                if order.status != "pending":
                    continue  # paid or cancelled while we were looping
                cancel_order(order=order, reason="Payment not completed in time.")
                cancelled += 1
        except Exception:
            logger.exception("Failed to expire order %s", pk)
    return cancelled


@shared_task
def cancel_expired_pending_orders():
    return expire_pending_orders()

  