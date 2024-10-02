from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, TaskWorkSession, Task
from django.utils.timezone import now


class CurrentTaskTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")

    def test_not_authenticated(self):
        response = self.client.get(reverse("current_task"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("current_task"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})

        task = Task.objects.create(owner=self.user_1, description="Test 123")
        TaskWorkSession.objects.create(
            task=task,
            user=self.user_1,
            started_at=now(),
        )

        response = self.client.get(reverse("current_task"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("description"), task.description)

        response = self.client.get(
            reverse("current_task") + f"?user={self.user_2.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("description"), None)

        task_2 = Task.objects.create(
            owner=self.user_2, description="Test 12345"
        )
        TaskWorkSession.objects.create(
            task=task_2,
            user=self.user_2,
            started_at=now(),
        )

        response = self.client.get(
            reverse("current_task") + f"?user={self.user_2.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("description"), None)
