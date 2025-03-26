from django.core.management.base import BaseCommand
from core.models import Beacon, User, TaskWorkSession, Log
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    def handle(self, *args, **options):
        """This command would run via cron or periodic task every minute or so,
        but Beacons are to be created randomly for user"""

        cutoff_time = timezone.now() - timedelta(minutes=30)
        for tws in TaskWorkSession.objects.filter(
            stopped_at__isnull=True, started_at__lte=cutoff_time
        ):
            beacon = Beacon.objects.filter(
                user=tws.user, confirmed_at__isnull=True
            ).first()

            if not beacon:
                beacon = Beacon.objects.create(user=tws.user)
                print(f"Beacon {beacon.id} created for {tws.user}")

        # find active Beacons if older than 10 mins - stop working on task
        cutoff_time = timezone.now() - timedelta(minutes=10)
        for beacon in Beacon.objects.filter(
            confirmed_at__isnull=True, created_at__lte=cutoff_time
        ):
            Beacon.close_for_user(beacon.user)

            tws = TaskWorkSession.objects.filter(
                user=beacon.user, stopped_at__isnull=True
            ).first()
            if tws:
                tws.stopped_at = timezone.now()
                tws.save()

                _msg = f"Beacon not confirmed in time. Stopping work on task [{tws.task}] [{beacon.user}]"
                Log.objects.create(
                    task=tws.task,
                    user=beacon.user,
                    message=_msg,
                )
