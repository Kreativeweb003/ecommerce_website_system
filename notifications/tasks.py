from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, *, event_type, recipient, subject, template_name, context, user_id=None, reference=""):
    from .models import NotificationLog

    log = NotificationLog.objects.create(
        user_id=user_id,
        channel="email",
        event_type=event_type,
        recipient=recipient,
        subject=subject,
        reference=reference,
        status="pending",
    )

    try:
        html_body = render_to_string(f"notifications/emails/{template_name}.html", context)
        text_body = strip_tags(html_body)

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()

        log.status = "sent"
        log.body_preview = text_body[:500]
        from django.utils import timezone
        log.sent_at = timezone.now()
        log.save(update_fields=["status", "body_preview", "sent_at"])

    except Exception as exc:
        log.status = "failed"
        log.failure_reason = str(exc)[:255]
        log.save(update_fields=["status", "failure_reason"])
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(self, *, event_type, recipient, message, user_id=None, reference=""):
    from .models import NotificationLog

    log = NotificationLog.objects.create(
        user_id=user_id,
        channel="sms",
        event_type=event_type,
        recipient=recipient,
        body_preview=message[:500],
        reference=reference,
        status="pending",
    )

    try:
        # Plug in your SMS provider here (Twilio, Termii, etc.)
        # Example (Twilio):
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to=recipient)

        log.status = "sent"
        from django.utils import timezone
        log.sent_at = timezone.now()
        log.save(update_fields=["status", "sent_at"])

    except Exception as exc:
        log.status = "failed"
        log.failure_reason = str(exc)[:255]
        log.save(update_fields=["status", "failure_reason"])
        raise self.retry(exc=exc)