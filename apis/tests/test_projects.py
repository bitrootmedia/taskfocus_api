import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Project, User, ProjectAccess


class ProjectTests(APITestCase):
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
            is_closed=True,
        )
        cls.project_3 = Project.objects.create(
            title="Testing Project 3",
            owner=cls.user_3,
            description="Description of project 3",
            is_closed=True
        )

        ProjectAccess.objects.create(project=cls.project_3, user=cls.user)

    def test_api_project_list_not_authenticated(self):
        response = self.client.get(reverse("project_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_project_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("project_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.project)
        self.assertNotContains(response, self.project_2)
        self.assertContains(response, self.project_3)
        self.assertEqual(json.loads(response.content).get("count"), 2)

    def test_api_project_list_filter(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("project_list") + "?title=" + self.project.title
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.project)
        self.assertNotContains(response, self.project_2)
        self.assertNotContains(response, self.project_3)
        self.assertEqual(json.loads(response.content).get("count"), 1)

    def test_api_project_details_not_logged_in(self):
        response = self.client.get(
            reverse("project_detail", kwargs={"pk": self.project.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_project_details_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("project_detail", kwargs={"pk": self.project.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.project.title)
        self.assertContains(response, self.project.description)

    def test_api_project_not_owner_no_access_details(self):
        self.client.force_login(self.user_3)
        response = self.client.get(
            reverse("project_detail", kwargs={"pk": self.project.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_project_not_owner_details_has_access(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("project_detail", kwargs={"pk": self.project_3.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_project_update_own_project(self):
        self.client.force_login(self.user)
        updated_title = "Updated title in project 1"
        self.client.put(
            reverse("project_detail", kwargs={"pk": self.project.id}),
            {"title": updated_title},
        )

        r = self.client.get(
            reverse("project_detail", kwargs={"pk": self.project.id})
        )
        self.assertContains(r, updated_title)

    def test_api_project_update_not_own_project(self):
        self.client.force_login(self.user)
        updated_title = "Updated title in project 3"
        self.client.put(
            reverse("project_detail", kwargs={"pk": self.project_3.id}),
            {"title": updated_title},
        )

        r = self.client.get(
            reverse("project_detail", kwargs={"pk": self.project_3.id})
        )
        self.assertContains(r, updated_title)

    def test_api_project_update_no_access_project(self):
        self.client.force_login(self.user)
        updated_title = "Updated title in project 2"
        s = self.client.put(
            reverse("project_detail", kwargs={"pk": self.project_2.id}),
            {"title": updated_title},
        )
        self.assertEqual(s.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_destroy_project(self):
        self.client.force_login(self.user)
        s = self.client.delete(
            reverse("project_detail", kwargs={"pk": self.project_2.id})
        )
        self.assertEqual(s.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_change_project_owner(self):
        self.client.force_login(self.user)
        s = self.client.post(
            reverse("project_owner_change", kwargs={"pk": self.project.pk}),
            data={"owner": str(self.user_3.id)},
        )

        self.assertEqual(s.status_code, status.HTTP_200_OK)

    
    def test_api_project_list_filter_closed(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("project_list") + "?show_closed=False"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.project)
        self.assertNotContains(response, self.project_2)
        self.assertNotContains(response, self.project_3)
        self.assertEqual(json.loads(response.content).get("count"), 1)