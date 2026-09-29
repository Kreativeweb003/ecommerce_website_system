from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        if not settings.DEBUG and not settings.CELERY_TASK_ALWAYS_EAGER:
            logger.info(
                "Notifications running in async mode — ensure a Celery worker process is running, "
                "or emails/SMS will queue indefinitely without being sent."
            )



  