import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Project, User, ProjectAccess


class UsersTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

    def test_api_user_list_not_authenticated(self):
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_user_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_ids = [x.get("id") for x in response.json().get("results")]
        user_names = [
            x.get("username") for x in response.json().get("results")
        ]

        self.assertIn(str(self.user.id), user_ids)
        self.assertIn(str(self.user_2.id), user_ids)
        self.assertIn(str(self.user_3.id), user_ids)

        self.assertIn(self.user.username, user_names)
        self.assertIn(self.user_2.username, user_names)
        self.assertIn(self.user_3.username, user_names)
