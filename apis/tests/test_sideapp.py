import json

from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Reminder, Task, User


class SideAppTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")
        cls.task_1 = Task.objects.create(owner=cls.user_1, title="Test")
        cls.task_2 = Task.objects.create(owner=cls.user_1, title="Test 2")
        cls.reminder_1 = Reminder.objects.create(
            created_by=cls.user_1,
            user=cls.user_1,
            task=cls.task_1,
            reminder_date=now(),
        )

    def test_api_not_authenticated(self):
        response = self.client.get(reverse("sideapp_home"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(reverse("sideapp_home"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_authenticated(self):
        self.client.force_login(self.user_1)
        data = {"quick_action": "test"}
        response = self.client.post(
            reverse("sideapp_home"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
