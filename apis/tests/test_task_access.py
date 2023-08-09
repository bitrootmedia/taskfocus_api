from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Project, User, ProjectAccess, TaskAccess, Task


class TaskAccessTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")
        cls.user_4 = User.objects.create(username="user4")
        cls.user_5 = User.objects.create(username="user5")
        cls.user_6 = User.objects.create(username="user6")

        cls.project_1_user_1 = Project.objects.create(
            title="Testing Project 1 XXX",
            owner=cls.user_1,
            description="Description of project 1",
        )
        cls.project_2_user_2 = Project.objects.create(
            title="Testing Project 2",
            owner=cls.user_2,
            description="Description of project 2",
        )
        cls.project_3_user_3 = Project.objects.create(
            title="Testing Project 3",
            owner=cls.user_3,
            description="Description of project 3",
        )

        cls.project_access_project_1_user_1__user2 = (
            ProjectAccess.objects.create(
                project=cls.project_1_user_1, user=cls.user_2
            )
        )

        cls.project_access_project_1_user_1__user5 = (
            ProjectAccess.objects.create(
                project=cls.project_1_user_1, user=cls.user_5
            )
        )

        cls.project_access_project_1_user_1__user6 = (
            ProjectAccess.objects.create(
                project=cls.project_1_user_1, user=cls.user_6
            )
        )

        cls.task_1_user_1 = Task.objects.create(
            owner=cls.user_1, title="What to do"
        )

        cls.task_1_user_1_access = TaskAccess.objects.create(
            task=cls.task_1_user_1, user=cls.user_1
        )

        cls.task_2_user_1 = Task.objects.create(
            owner=cls.user_1, title="What to do next"
        )

        cls.task_2_user_1_access = TaskAccess.objects.create(
            task=cls.task_2_user_1, user=cls.user_1
        )

        cls.task_3_user_3 = Task.objects.create(
            owner=cls.user_3, title="What to do next"
        )

    def test_api_task_access_list_not_authenticated(self):
        response = self.client.get(reverse("task_access_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_task_access_list_authenticated(self):
        self.client.force_login(self.user_1)
        response = self.client.get(
            reverse("task_access_list") + f"?task={self.task_1_user_1.pk}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json().get("results")

        found = False
        for res in results:
            if res.get("task") == self.task_1_user_1.id.__str__():
                if res.get("user").get("id") == self.user_1.id.__str__():
                    found = True

        self.assertTrue(found)

    def test_api_task_access_list_authenticated_with_filter(self):
        self.client.force_login(self.user_1)
        response = self.client.get(
            reverse("task_access_list") + f"?task={self.task_1_user_1.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json().get("results")
        task_users_id_api = [r.get("user").get("id") for r in results]
        task_users_id_db = [
            f"{u.user.id}"
            for u in TaskAccess.objects.filter(task=self.task_1_user_1)
        ]

        self.assertEqual(set(task_users_id_db), set(task_users_id_api))

    def test_api_task_access_create(self):
        self.client.force_login(self.user_1)

        self.assertFalse(
            TaskAccess.objects.filter(
                task=self.task_1_user_1, user=self.user_3
            ).exists()
        )

        response = self.client.post(
            reverse("task_access_list"),
            {"task": self.task_1_user_1.id, "user": self.user_3.id},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            TaskAccess.objects.filter(
                task=self.task_1_user_1, user=self.user_3
            ).exists()
        )

    def test_api_task_access_create_not_owner(self):
        self.client.force_login(self.user_1)

        self.assertFalse(
            TaskAccess.objects.filter(
                task=self.task_3_user_3, user=self.user_2
            ).exists()
        )

        response = self.client.post(
            reverse("task_access_list"),
            {"task": self.task_3_user_3.id, "user": self.user_2.id},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(
            TaskAccess.objects.filter(
                task=self.task_3_user_3, user=self.user_2
            ).exists()
        )

    def test_api_task_access_delete_project_not_owner(self):
        self.client.force_login(self.user_1)

        pa = TaskAccess.objects.create(
            task=self.task_3_user_3, user=self.user_2
        )

        response = self.client.delete(
            reverse("task_access_detail", kwargs={"pk": pa.id.__str__()})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # TODO: finish tests
    # def test_api_task_access_update(self):
    #     self.client.force_login(self.user_1)
    #     response = self.client.put(
    #         reverse(
    #             "task_access_detail",
    #             kwargs={
    #                 "pk": self.task_1_user_1_access.id.__str__()
    #             },
    #         ),
    #         {
    #             "user": self.user_3.id.__str__(),
    #             "project": self.project_3_user_3.id.__str__(),
    #         },
    #     )
    #
    #     self.assertEqual(
    #         response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
    #     )
    #
    # def test_api_project_access_delete_project_owner(self):
    #     self.client.force_login(self.user_1)
    #     pa = ProjectAccess.objects.create(
    #         project=self.project_1_user_1, user=self.user_4
    #     )
    #     response = self.client.delete(
    #         reverse("project_access_detail", kwargs={"pk": pa.id.__str__()})
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    #
    # def test_api_project_access_details_not_authenticated(self):
    #     pa = ProjectAccess.objects.create(
    #         project=self.project_1_user_1, user=self.user_4
    #     )
    #     response = self.client.get(
    #         reverse("project_access_detail", kwargs={"pk": pa.id.__str__()})
    #     )
    #
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
