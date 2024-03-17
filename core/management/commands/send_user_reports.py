import calendar
import logging

import pytz
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import UserReportsSchedule
from core.utils.send_user_report import send_user_report

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """To work properly this command should run every 30 minutes starting from 00:00, that is 00:30, 01:00, etc."""

    help = 'Send user reports (takes no args/kwargs)'

    def handle(self, *args, **options):
        # We're calculating UTC times dynamically in for loops to
        #   adjust for DST (DaylightSavingsTime) cause that can be tricky to pull off properly.

        try:
            current_time_utc = timezone.now()  # UTC
            current_time_utc_str = current_time_utc.strftime('%H:%M')

            today = current_time_utc.date()
            week_ago = today - relativedelta(days=7)
            month_ago = today - relativedelta(months=1)

            # --- Send daily at given time ---

            daily_schedules = UserReportsSchedule.objects.filter(
                daily_enabled=True,
                daily_time__isnull=False
            )

            for schedule in daily_schedules:
                self.check_time_and_send_user_report(
                    today, today, "daily_time",
                    today, current_time_utc_str, schedule
                )

            # --- Send weekly at given time ---

            weekly_schedules = UserReportsSchedule.objects.filter(
                weekly_enabled=True,
                weekly_day=today.weekday(),
                weekly_time__isnull=False,
            )

            for schedule in weekly_schedules:
                self.check_time_and_send_user_report(
                    week_ago, today, "weekly_time",
                    today, current_time_utc_str, schedule
                )

            # --- Send monthly at given time ---

            # We should send reports on the last day of the month
            #  if user's "monthly_day" exceeds maximum available that month
            #  4ex. on 28th (or 29th) of Feb. users with monthly_day=31 should get the report as well.
            #

            _, last_day_of_month = calendar.monthrange(today.year, today.month)
            if last_day_of_month < 31 and today.day == last_day_of_month:
                monthly_valid_days = [i for i in range(last_day_of_month, 32)]
            else:
                monthly_valid_days = [today.day, ]

            monthly_schedules = UserReportsSchedule.objects.filter(
                monthly_enabled=True,
                monthly_day__in=monthly_valid_days,
                monthly_time__isnull=False
            )

            for schedule in monthly_schedules:
                self.check_time_and_send_user_report(
                    month_ago, today, "monthly_time",
                    today, current_time_utc_str, schedule
                )
        except Exception as ex:
            self.stderr.write(f"Unhandled command error: {ex}")

    def check_time_and_send_user_report(
            self, start_date, end_date, time_field_name,
            today, current_time_utc_str, schedule
    ):
        """ Convert time in specified timezone to UTC and check if we should send given report type. """

        try:
            tz = pytz.timezone(schedule.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            self.stderr.write(f"Couldn't get the timezone, schedule.id: {schedule.id}, tz value: {schedule.timezone}")
            return

        report_type_time = getattr(schedule, time_field_name)
        if not report_type_time:
            self.stderr.write(f"No time given for specified report type: {time_field_name}")
            return

        calculated_time_utc = UserReportsSchedule.utc_time_str_from_time_and_date_with_tz(
            report_type_time, tz, today
        )

        if calculated_time_utc == current_time_utc_str:
            period_label = time_field_name.replace("_time", "")

            send_user_report(start_date, end_date, schedule.user.email, period_label, user_id=schedule.user.id)
            self.stdout.write(f"Successfully sent {period_label} report to: {schedule.user.email}")
