import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Task, TaskWorkSession, User


class WorkSessionBreakdownTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")

        cls.task_1 = Task.objects.create(owner=cls.user, title="Task 1", description="Task 1 Description")
        cls.task_2 = Task.objects.create(owner=cls.user, title="Task 2", description="Task 2 Description")
        cls.base_dt = datetime.datetime(
            2024,
            1,
            1,
            10,
        )  # 10:00 2024-01-01
        cls.next_day = cls.base_dt + datetime.timedelta(days=1)
        cls.work_session_1 = TaskWorkSession.objects.create(  # 10:00 - 10:20
            started_at=cls.base_dt,
            stopped_at=cls.base_dt + datetime.timedelta(minutes=20),
            task=cls.task_1,
            user=cls.user,
        )
        cls.work_session_2 = TaskWorkSession.objects.create(  # 10:30 - 11:00
            started_at=cls.base_dt + datetime.timedelta(minutes=30),
            stopped_at=cls.base_dt + datetime.timedelta(hours=1),
            task=cls.task_1,
            user=cls.user,
        )

        cls.work_session_3 = TaskWorkSession.objects.create(  # 10:30 - 11:00
            started_at=cls.base_dt + datetime.timedelta(hours=24),
            stopped_at=cls.base_dt + datetime.timedelta(hours=24, minutes=30),
            task=cls.task_2,
            user=cls.user,
        )

    def test_work_session_breakdown(self):
        # TODO: Add authorization - staff only?
        self.client.force_authenticate(user=self.user)

        r = self.client.post(
            reverse("work_sessions_breakdown"),
            data={
                "user_id": self.user.id,
                "start_date": self.base_dt.strftime("%Y-%m-%d"),
                "end_date": self.next_day.strftime("%Y-%m-%d"),
            },
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_no_sessions(self):
        self.client.force_authenticate(user=self.user_2)
        r = self.client.post(
            reverse("work_sessions_breakdown"),
            data={
                "user_id": self.user_2.id,
                "start_date": self.base_dt.strftime("%Y-%m-%d"),
                "end_date": self.next_day.strftime("%Y-%m-%d"),
            },
        )

        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_missing_data(self):
        self.client.force_authenticate(user=self.user_2)
        r = self.client.post(
            reverse("work_sessions_breakdown"),
            data={
                "user_id": self.user.id,
            },
        )

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
