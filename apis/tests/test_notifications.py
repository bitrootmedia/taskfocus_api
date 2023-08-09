from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, Notification, NotificationAck


class NotificationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")
        cls.notification_1_no_task_no_project_no_comment = (
            Notification.objects.create(
                tag="testing tag", content="This is an example"
            )
        )
        NotificationAck.objects.create(
            user=cls.user_1,
            notification=cls.notification_1_no_task_no_project_no_comment,
        )

    def test_notifications_not_authenticated(self):
        response = self.client.get(reverse("notifications"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_notifications_authenticated(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("notifications") + "?status=UNREAD")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get("count"), 1)

        self.client.post(
            reverse(
                "confirm_notification",
                kwargs={"pk": data.get("results")[0].get("id")},
            )
        )

        response = self.client.get(reverse("notifications") + "?status=UNREAD")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get("count"), 0)
