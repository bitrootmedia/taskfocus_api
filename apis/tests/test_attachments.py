from unittest import skip

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Attachment, Project, ProjectAccess, Task, TaskAccess, User


class AttachmentTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

        cls.project_1 = Project.objects.create(
            title="Testing Project 1 XXX",
            owner=cls.user_1,
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

        ProjectAccess.objects.create(project=cls.project_3, user=cls.user_1)
        ProjectAccess.objects.create(project=cls.project_1, user=cls.user_2)

        cls.task_1_project_1_user_1 = Task.objects.create(project=cls.project_1, owner=cls.user_1, title="Task 1")

        cls.attachment_1_project_1_user_1 = Attachment.objects.create(project=cls.project_1, owner=cls.user_1)

        cls.attachment_2_project_2_user_2 = Attachment.objects.create(project=cls.project_2, owner=cls.user_2)

        cls.attachment_3_project_3_user_3 = Attachment.objects.create(project=cls.project_3, owner=cls.user_3)

        cls.attachment_4_project_1_task_1 = Attachment.objects.create(
            project=cls.project_1,
            task=cls.task_1_project_1_user_1,
            owner=cls.user_1,
        )

    def test_attachment_list_not_authenticated(self):
        response = self.client.get(reverse("attachment_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_attachment_list_authenticated(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("attachment_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_attachment_list_user_in_task_not_in_project(self):
        TaskAccess.objects.create(user=self.user_3, task=self.task_1_project_1_user_1)
        self.client.force_login(self.user_3)
        response = self.client.get(reverse("attachment_list") + f"?task={self.task_1_project_1_user_1.id}")
        attachment_ids = [x.get("id") for x in response.json().get("results", [])]
        self.assertIn(str(self.attachment_4_project_1_task_1.id), attachment_ids)

    def test_attachment_no_access(self):
        self.client.force_login(self.user_3)
        response = self.client.get(reverse("attachment_list"))
        attachment_ids = [x.get("id") for x in response.json().get("results", [])]
        self.assertNotIn(str(self.attachment_1_project_1_user_1.id), attachment_ids)

    def test_attachment_filter_project(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("attachment_list") + f"?project={self.project_3.id}")
        attachment_ids = [x.get("id") for x in response.json().get("results", [])]
        self.assertIn(str(self.attachment_3_project_3_user_3.id), attachment_ids)
        self.assertNotIn(str(self.attachment_1_project_1_user_1.id), attachment_ids)

    def test_attachment_filter_task(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("attachment_list") + f"?task={self.task_1_project_1_user_1.id}")
        attachment_ids = [x.get("id") for x in response.json().get("results", [])]
        self.assertIn(str(self.attachment_4_project_1_task_1.id), attachment_ids)
        self.assertNotIn(str(self.attachment_1_project_1_user_1.id), attachment_ids)

    def test_attachment_access_owner(self):
        self.client.force_login(self.user_3)
        response = self.client.get(reverse("attachment_list"))
        attachment_ids = [x.get("id") for x in response.json().get("results", [])]
        self.assertIn(str(self.attachment_3_project_3_user_3.id), attachment_ids)

    def test_attachment_project_access(self):
        self.client.force_login(self.user_1)
        response = self.client.get(reverse("attachment_list"))
        attachment_ids = [x.get("id") for x in response.json().get("results", [])]
        self.assertIn(str(self.attachment_3_project_3_user_3.id), attachment_ids)

    def test_create_attachment_no_auth(self):
        response = self.client.post(
            reverse("attachment_list"),
            {
                "project": self.project_1.id,
                "title": "Attachment 1 Created By API",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @skip("Skipped until its fixed")
    def test_create_attachment(self):
        self.client.force_login(self.user_1)
        response = self.client.post(
            reverse("attachment_list"),
            {
                "project": self.project_1.id,
                "owner": self.user_1,
                "title": "Attachment 1 Created By API",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_own_attachment(self):
        self.client.force_login(self.user_1)
        updated_title = "This is an updated title"
        response = self.client.put(
            reverse(
                "attachment_detail",
                kwargs={"pk": self.attachment_1_project_1_user_1.id.__str__()},
            ),
            {"title": updated_title},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.attachment_1_project_1_user_1.refresh_from_db()
        self.assertEqual(updated_title, self.attachment_1_project_1_user_1.title)

    def test_update_somebody_elses_attachment(self):
        self.client.force_login(self.user_2)
        updated_title = "This is an updated title"
        response = self.client.put(
            reverse(
                "attachment_detail",
                kwargs={"pk": self.attachment_1_project_1_user_1.id.__str__()},
            ),
            {"title": updated_title},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_attachment(self):
        self.client.force_login(self.user_1)
        response = self.client.delete(
            reverse(
                "attachment_detail",
                kwargs={"pk": self.attachment_1_project_1_user_1.id.__str__()},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(
            reverse(
                "attachment_detail",
                kwargs={"pk": self.attachment_1_project_1_user_1.id.__str__()},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
