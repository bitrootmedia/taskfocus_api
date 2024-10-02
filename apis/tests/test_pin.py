from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Project, User, ProjectAccess, Task, Pin


class PinTests(APITestCase):
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

        cls.pin_task_2 = Pin.objects.create(
            user=cls.user_2,
            task=cls.task_2,
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

    def test_list_task_pins(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(reverse('pinned_task_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_pin_no_task_access(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(reverse('pin_task_detail', kwargs={"task_id": str(self.task_3.id)}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_pin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('pin_task_detail', kwargs={"task_id": str(self.task_3.id)}))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_pin_already_pinned(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(reverse('pin_task_detail', kwargs={"task_id": str(self.task_2.id)}))
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_delete_pin_no_task_access(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse('pin_task_detail', kwargs={"task_id": str(self.task_2.id)}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_pin(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(reverse('pin_task_detail', kwargs={"task_id": str(self.task_2.id)}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_pin_not_pinned(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse('pin_task_detail', kwargs={"task_id": str(self.task_3.id)}))
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)
