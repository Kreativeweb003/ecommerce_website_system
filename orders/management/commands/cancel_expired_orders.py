from django.core.management.base import BaseCommand

from orders.tasks import expire_pending_orders


class Command(BaseCommand):
    help = "Cancels unpaid pending orders past the expiry window and releases their reserved stock."

    def handle(self, *args, **options):
        count = expire_pending_orders()
        self.stdout.write(self.style.SUCCESS(f"Cancelled {count} expired order(s)."))



