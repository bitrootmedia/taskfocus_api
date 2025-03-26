from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Notification, NotificationAck, Task, User


class UserTaskQueueTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.task = Task.objects.create(owner=cls.user_1, title="Test")

    def test_user_task_queue_not_authenticated(self):
        response = self.client.get(reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_task_queue_authenticated(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_task_queue_authenticated_post(self):
        self.client.force_login(self.user_1)
        response = self.client.post(
            reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}),
            data={},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}))
        users = [x.get("id") for x in response.json().get("users")]
        self.assertTrue(f"{self.user_1.pk}" in users)

        self.client.delete(reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}))

        response = self.client.get(reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}))
        users = [x.get("id") for x in response.json().get("users")]
        self.assertTrue(f"{self.user_1.pk}" not in users)

    def test_user_task_queue_authenticated_post_user(self):
        self.client.force_login(self.user_1)
        response = self.client.post(
            reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}),
            data={"user": f"{self.user_2.pk}"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.post(
            reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}),
            data={"user": f"{self.user_1.pk}"},
        )

        response = self.client.get(reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}))
        users = [x.get("id") for x in response.json().get("users")]
        self.assertTrue(f"{self.user_2.pk}" in users)
        self.assertTrue(f"{self.user_1.pk}" in users)

        self.client.delete(
            reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}),
            data={"user": f"{self.user_2.pk}"},
        )

        response = self.client.get(reverse("user_task_queue_manage", kwargs={"pk": self.task.pk}))
        users = [x.get("id") for x in response.json().get("users")]
        self.assertTrue(f"{self.user_2.pk}" not in users)
