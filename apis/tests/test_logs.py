from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Log, Project, ProjectAccess, User


class LogsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

        cls.project = Project.objects.create(
            title="Testing Project 1 XXX",
            owner=cls.user,
            description="Description of project 1",
        )
        cls.project_2 = Project.objects.create(
            title="Testing Project 2",
            owner=cls.user_2,
            description="Description of project 2",
        )
        cls.project_3 = Project.objects.create(
            title="Testing Project 3",
            owner=cls.user_3,
            description="Description of project 3",
        )

        ProjectAccess.objects.create(project=cls.project_3, user=cls.user)

        cls.log_user_1_no_project = Log.objects.create(user=cls.user, message="User 1 No Project Log")

        cls.log_user_1_project_1 = Log.objects.create(user=cls.user, message="User 1 Project 1 Log")

        cls.log_user_2_project_2 = Log.objects.create(user=cls.user_2, message="User 2 Project 2 Log")

        cls.log_user_3_project_3 = Log.objects.create(
            user=cls.user_3,
            project=cls.project_3,
            message="User 3 Project 3 Log",
        )

    def test_log_list_not_authenticated(self):
        response = self.client.get(reverse("log_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_log_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("log_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_log_list_project_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("log_list"))
        self.assertIn(
            str(self.log_user_1_no_project.id),
            [x.get("id") for x in response.json().get("results")],
        )

    def test_log_list_project_not_owner_not_member(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("log_list"))
        self.assertNotIn(
            str(self.log_user_2_project_2.id),
            [x.get("id") for x in response.json().get("results")],
        )

    def test_log_list_project_member(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("log_list"))
        self.assertIn(
            str(self.log_user_3_project_3.id),
            [x.get("id") for x in response.json().get("results")],
        )
