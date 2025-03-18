from django.core.management.base import BaseCommand
from core.models import Beacon, User, TaskWorkSession


class Command(BaseCommand):
    def handle(self, *args, **options):
        # TODO: when task is stopped worked on - close active beacon
        # TODO: do not create beacon more often than X the previous one was created

        for tws in TaskWorkSession.objects.filter(stopped_at__isnull=True):
            beacon = Beacon.objects.filter(
                user=tws.user, confirmed_at__isnull=True
            ).first()
            if not beacon:
                beacon = Beacon.objects.create(user=tws.user)
                print(f"Beacon {beacon.id} created for {tws.user}")
