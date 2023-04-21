from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, Notification, NotificationAck


class NotificationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")

    def test_notification_not_authenticated(self):
        response = self.client.get(reverse("notifications"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # TODO: add all tests
