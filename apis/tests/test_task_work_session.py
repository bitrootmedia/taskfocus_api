from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Project, User, ProjectAccess, Task


class TasksSessionTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

        cls.task_1 = Task.objects.create(
            owner=cls.user, title="Task 1", description="Task 1 Description"
        )

        cls.project_2 = Project.objects.create(
            title="Testing Project 2",
            owner=cls.user_2,
            description="Description of project 2",
        )
        cls.task_2 = Task.objects.create(
            owner=cls.user_2,
            title="Task 2",
            description="Task 2 Description",
            project=cls.project_2,
        )

        cls.project_3 = Project.objects.create(
            title="Testing Project 3",
            owner=cls.user_3,
            description="Description of project 3",
        )

        cls.task_3 = Task.objects.create(
            owner=cls.user_3,
            title="Task 3",
            description="Task 3 Description",
            project=cls.project_3,
        )

        ProjectAccess.objects.create(project=cls.project_3, user=cls.user)

        cls.project_4 = Project.objects.create(
            title="Testing Project 4",
            owner=cls.user,
            description="Description of project 4",
        )

        cls.task_4 = Task.objects.create(
            owner=cls.user_3,
            title="Task 4",
            description="Task 4 Description",
            project=cls.project_4,
        )

    def test_task_start(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("task_start_work", kwargs={"pk": self.task_1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("message"), "Testing Start")

    def test_task_stop(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("task_stop_work", kwargs={"pk": self.task_1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("message"), "Testing Stop")
