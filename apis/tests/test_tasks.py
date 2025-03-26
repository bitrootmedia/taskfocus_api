from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Pin, Project, ProjectAccess, Task, User


class TasksTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

        cls.task_1 = Task.objects.create(owner=cls.user, title="Task 1", description="Task 1 Description")

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

        cls.task_5 = Task.objects.create(
            owner=cls.user_3,
            title="Task 5",
            description="Changing owner",
            project=cls.project_4,
        )

    def test_task_list_not_logged(self):
        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_list_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.task_1.title)
        self.assertNotContains(response, self.task_2.title)

    def test_task_list_project_member(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_list"))
        self.assertContains(response, self.task_3.title)

    def test_task_list_project_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_list"))
        self.assertContains(response, self.task_4.title)

    def test_task_detail_not_logged(self):
        response = self.client.get(reverse("task_detail", kwargs={"pk": self.task_1.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_detail_logged_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_detail", kwargs={"pk": self.task_1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_task_detail_logged_no_access(self):
        self.client.force_login(self.user_3)
        response = self.client.get(reverse("task_detail", kwargs={"pk": self.task_1.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_detail_logged_access_project_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_detail", kwargs={"pk": self.task_4.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_task_detail_logged_access_project_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_detail", kwargs={"pk": self.task_3.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_task_update_own(self):
        self.client.force_login(self.user)
        updated_title = "Updated title in project 1"
        r = self.client.put(
            reverse("task_detail", kwargs={"pk": self.task_1.id}),
            {"title": updated_title},
        )
        self.assertEqual(r.status_code, 200)

        r = self.client.get(reverse("task_detail", kwargs={"pk": self.task_1.id}))
        self.assertContains(r, updated_title)

    def test_api_task_update_no_access(self):
        self.client.force_login(self.user_3)
        updated_title = "Updated title in project 1"
        response = self.client.put(
            reverse("task_detail", kwargs={"pk": self.task_1.id}),
            {"title": updated_title},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_task_update_with_project_access_only(self):
        self.client.force_login(self.user)
        updated_title = "Updated title in project 4"
        self.client.put(
            reverse("task_detail", kwargs={"pk": self.task_4.id}),
            {"title": updated_title},
        )

        r = self.client.get(reverse("task_detail", kwargs={"pk": self.task_4.id}))
        self.assertContains(r, updated_title)

    def test_api_task_update_project(self):
        self.client.force_login(self.user)
        new_project = Project.objects.create(title="one", owner=self.user)
        r = self.client.patch(
            reverse("task_detail", kwargs={"pk": self.task_4.id}),
            {"project": new_project.id},
        )
        self.assertEqual(r.status_code, 200)

    def test_api_task_delete(self):
        self.client.force_login(self.user)
        response = self.client.delete(reverse("task_detail", kwargs={"pk": self.task_4.id}))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_api_task_create(self):
        self.client.force_login(self.user)
        title = "This is the title"
        response = self.client.post(reverse("task_list"), {"title": title})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_task_id = response.json().get("id")
        task_db = Task.objects.get(pk=created_task_id)
        self.assertEqual(task_db.owner, self.user)
        self.assertEqual(task_db.title, title)
        self.assertEqual(task_db.project, None)

    def test_task_change_owner(self):
        self.client.force_login(self.user)
        # r = self.client.put(
        #     reverse("task_detail", kwargs={"pk": self.task_1.id}),
        #     {"owner": f"{self.user_2.pk}"},
        # )
        # self.assertEqual(r.status_code, 200)

        # r = self.client.get(
        #     reverse("task_detail", kwargs={"pk": self.task_1.id})
        # )
        # self.assertContains(r, "as")

    # TODO: only task owner and project owner can change task owner
    def test_task_change_owner_not_task_owner(self):
        ...

    def test_task_detail_is_pinned(self):
        self.client.force_login(self.user)
        request = self.client.get(reverse("task_detail", kwargs={"pk": self.task_1.id}))
        self.assertFalse(request.json().get("is_pinned"))

        Pin.objects.create(user=self.user, task=self.task_1)
        request = self.client.get(reverse("task_detail", kwargs={"pk": self.task_1.id}))
        self.assertTrue(request.json().get("is_pinned"))
