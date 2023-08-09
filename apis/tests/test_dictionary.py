from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User


class DictionaryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")

    def test_dictionary_not_authenticated(self):
        response = self.client.get(reverse("dictionary_view"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dictionary_authenticated(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("dictionary_view"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(response.json().get("task_status_choices"))
        self.assertTrue(response.json().get("task_urgency_level_choices"))
