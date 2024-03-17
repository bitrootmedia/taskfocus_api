import datetime
from io import StringIO
from unittest import mock

import pytz
from dateutil.relativedelta import relativedelta
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core.models import Task, TaskWorkSession, User, UserReportsSchedule
from core.utils.send_user_report import _get_email_subject

BASE_DT_NOW = datetime.datetime(year=2020, month=1, day=10, hour=8, minute=30, tzinfo=pytz.UTC)


class TestSendUserReportsCommand(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user", email="user@some.domain")
        cls.user_2 = User.objects.create(username="user2", email="user2@some.domain")

        cls.task_1 = Task.objects.create(
            owner=cls.user, title="Task 1", description="Task 1 worked on today"
        )

        cls.task_1_work_session = TaskWorkSession.objects.create(
            started_at=BASE_DT_NOW - datetime.timedelta(hours=1),
            stopped_at=BASE_DT_NOW,
            user=cls.user
        )

        cls.task_2 = Task.objects.create(
            owner=cls.user, title="Task 2", description="Task 2 worked on 6 days ago"
        )

        cls.task_2_work_session = TaskWorkSession.objects.create(
            started_at=BASE_DT_NOW - datetime.timedelta(days=6),
            stopped_at=BASE_DT_NOW - datetime.timedelta(days=5, hours=22),
            user=cls.user
        )

        cls.schedule_user = UserReportsSchedule.objects.create(
            user=cls.user,
            timezone="UTC",
            daily_enabled=True,
            daily_time="08:30",
            weekly_enabled=True,
            weekly_day=4,  # Friday (2020-01-10)
            weekly_time="10:00",
            monthly_enabled=True,
            monthly_day=10,
            monthly_time="11:30",
        )

        cls.schedule_user_2 = UserReportsSchedule.objects.create(
            user=cls.user_2,
            timezone="Canada/Central",
            daily_enabled=False,
            daily_time="17:30",
            weekly_enabled=True,
            monthly_enabled=False
        )

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "send_user_reports",
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    def test_daily_schedule(self):
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=BASE_DT_NOW)):
            current_time_utc = timezone.now()
            self.assertEqual(current_time_utc, BASE_DT_NOW)

            out = self.call_command()
            self.assertEqual(out, f"Successfully sent daily report to: {self.user.email}\n")
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                _get_email_subject("daily", self.user.username, BASE_DT_NOW, BASE_DT_NOW)
            )

    def test_weekly_schedule(self):
        dt_10am = datetime.datetime(year=2020, month=1, day=10, hour=10, minute=0, tzinfo=pytz.UTC)
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=dt_10am)):
            out = self.call_command()
            self.assertEqual(out, f"Successfully sent weekly report to: {self.user.email}\n")
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                _get_email_subject(
                    "weekly",
                    self.user.username,
                    dt_10am - datetime.timedelta(days=7),
                    dt_10am
                )
            )

    def test_monthly_schedule(self):
        dt_1130am = datetime.datetime(year=2020, month=1, day=10, hour=11, minute=30, tzinfo=pytz.UTC)
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=dt_1130am)):
            out = self.call_command()
            self.assertEqual(out, f"Successfully sent monthly report to: {self.user.email}\n")
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                _get_email_subject(
                    "monthly",
                    self.user.username,
                    dt_1130am - relativedelta(months=1),
                    dt_1130am
                )
            )

    def test_all_mails_at_once_in_order(self):
        UserReportsSchedule.objects.filter(id=self.schedule_user.id).update(
            timezone="UTC",
            daily_enabled=True,
            daily_time="08:30",
            weekly_enabled=True,
            weekly_day=4,  # Friday (10-01-2020)
            weekly_time="08:30",
            monthly_enabled=True,
            monthly_day=10,
            monthly_time="08:30",
        )

        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=BASE_DT_NOW)):
            out = self.call_command()
            self.assertEqual(
                out,
                (
                    f"Successfully sent daily report to: {self.user.email}\n"
                    f"Successfully sent weekly report to: {self.user.email}\n"
                    f"Successfully sent monthly report to: {self.user.email}\n"
                )
            )
            self.assertEqual(len(mail.outbox), 3)
            self.assertEqual(
                mail.outbox[0].subject,
                _get_email_subject(
                    "daily",
                    self.user.username,
                    BASE_DT_NOW,
                    BASE_DT_NOW
                )
            )
            self.assertEqual(
                mail.outbox[1].subject,
                _get_email_subject(
                    "weekly",
                    self.user.username,
                    BASE_DT_NOW - relativedelta(days=7),
                    BASE_DT_NOW,
                )
            )
            self.assertEqual(
                mail.outbox[2].subject,
                _get_email_subject(
                    "monthly",
                    self.user.username,
                    BASE_DT_NOW - relativedelta(months=1),
                    BASE_DT_NOW
                )
            )

    def test_monthly_on_31st_on_feb(self):
        # Schedule should be sent on the last day of the month if
        # monthly_day exceeds last valid day of the month (4ex. 31st on feb)
        self.schedule_user.monthly_day = 31
        self.schedule_user.save()

        dt_28th_feb = datetime.datetime(year=2023, month=2, day=28, hour=11, minute=30, tzinfo=pytz.UTC)

        # Add single work sessions so email gets sent
        self.task_1_work_session.started_at = dt_28th_feb - relativedelta(hours=5)
        self.task_1_work_session.stopped_at = dt_28th_feb
        self.task_1_work_session.save()

        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=dt_28th_feb)):
            out = self.call_command()
            self.assertEqual(out, f"Successfully sent monthly report to: {self.user.email}\n")
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                _get_email_subject(
                    "monthly",
                    self.user.username,
                    dt_28th_feb - relativedelta(months=1),
                    dt_28th_feb
                )
            )

    def test_daily_no_entry(self):
        dt_1730 = datetime.datetime(year=2020, month=1, day=10, hour=17, minute=30, tzinfo=pytz.UTC)
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=dt_1730)):
            out = self.call_command()
            self.assertEqual(len(mail.outbox), 0)
            self.assertEqual(out, "")

    def test_daily_no_schedules_fit(self):
        dt_0230 = datetime.datetime(year=2020, month=1, day=10, hour=2, minute=30, tzinfo=pytz.UTC)
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=dt_0230)):
            out = self.call_command()
            self.assertEqual(len(mail.outbox), 0)
            self.assertEqual(out, "")
