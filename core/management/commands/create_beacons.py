import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Beacon, Log, TaskWorkSession, User


class Command(BaseCommand):
    def handle(self, *args, **options):
        """This command would run via cron or periodic task every minute or so,
        but Beacons are to be created randomly for user"""
        beacon_time_cutoff = random.randint(
            settings.CREATE_BEACONS_INTERVAL_TIME_MIN, settings.CREATE_BEACONS_INTERVAL_TIME_MAX
        )

        cutoff_time = timezone.now() - timedelta(minutes=beacon_time_cutoff)
        for tws in TaskWorkSession.objects.filter(
            stopped_at__isnull=True, started_at__lte=cutoff_time, user__use_beacons=True
        ):
            if Beacon.objects.filter(user=tws.user, confirmed_at__isnull=True).exists():
                continue

            last_beacon = Beacon.objects.filter(user=tws.user).order_by("-created_at").first()

            if (
                last_beacon
                and last_beacon.confirmed_at
                and last_beacon.confirmed_at >= timezone.now() - timedelta(minutes=beacon_time_cutoff)
            ):
                continue

            beacon = Beacon.objects.create(user=tws.user)
            print(f"Beacon {beacon.id} created for {tws.user}")

        # find active Beacons if older than 10 mins - stop working on task
        cutoff_time = timezone.now() - timedelta(minutes=settings.CREATE_BEACONS_ALLOWED_CLICK_TIME)
        for beacon in Beacon.objects.filter(confirmed_at__isnull=True, created_at__lte=cutoff_time):
            Beacon.close_for_user(beacon.user)

            tws = TaskWorkSession.objects.filter(user=beacon.user, stopped_at__isnull=True).first()
            if tws:
                tws.stopped_at = timezone.now()
                tws.save()

                _msg = f"Beacon not confirmed in time. Stopping work on task [{tws.task}] [{beacon.user}]"
                Log.objects.create(
                    task=tws.task,
                    user=beacon.user,
                    message=_msg,
                )
