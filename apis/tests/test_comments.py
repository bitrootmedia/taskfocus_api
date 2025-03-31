from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Comment, Project, ProjectAccess, Task, User


class CommentTests(APITestCase):
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
        ProjectAccess.objects.create(project=cls.project, user=cls.user_2)

        cls.task_1_project_1_user_1 = Task.objects.create(project=cls.project, owner=cls.user, title="Task 1")

        cls.comment_1_task_1_user_2 = Comment.objects.create(
            task=cls.task_1_project_1_user_1,
            project=cls.project,
            author=cls.user_2,
            content="Comment 1 task 1 user 2",
        )

        cls.task_2_project_2_user_2 = Task.objects.create(project=cls.project_2, owner=cls.user_2, title="Task 2")

        cls.comment_2_task_2_user_2 = Comment.objects.create(
            task=cls.task_2_project_2_user_2,
            author=cls.user_2,
            content="Comment 2 task 2 user 2",
        )

        cls.comment_3_project_1_user_2 = Comment.objects.create(
            project=cls.project,
            author=cls.user_2,
            content="Comment 3 project 1 user 2",
        )

        cls.comment_4_project_1_user_1 = Comment.objects.create(
            project=cls.project,
            author=cls.user,
            content="Comment 4 project 1 user 1",
        )

    def test_comment_list_not_authenticated(self):
        response = self.client.get(reverse("comment_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("comment_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result_ids = [x.get("id") for x in response.json().get("results")]
        self.assertIn(
            self.comment_1_task_1_user_2.id.__str__(),
            result_ids,
        )

        self.assertNotIn(self.comment_2_task_2_user_2.id.__str__(), result_ids)

    def test_comment_list_project_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("comment_list"))
        result_ids = [x.get("id") for x in response.json().get("results")]
        self.assertIn(str(self.comment_3_project_1_user_2.id.__str__()), result_ids)

    def test_comment_list_project_not_owner_not_member(self):
        self.client.force_login(self.user_3)
        response = self.client.get(reverse("comment_list"))
        result_ids = [x.get("id") for x in response.json().get("results")]
        self.assertNotIn(str(self.comment_3_project_1_user_2.id.__str__()), result_ids)

    def test_comment_list_project_member(self):
        self.client.force_login(self.user_2)
        response = self.client.get(reverse("comment_list"))
        result_ids = [x.get("id") for x in response.json().get("results")]
        self.assertIn(str(self.comment_4_project_1_user_1.id), result_ids)

    def test_comment_list_project_filter(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("comment_list") + f"?project={self.project.id}")
        result_ids = [x.get("id") for x in response.json().get("results")]
        self.assertIn(str(self.comment_1_task_1_user_2.id), result_ids)
        self.assertNotIn(str(self.comment_2_task_2_user_2.id), result_ids)

    def test_create_comment_not_authenticated(self):
        response = self.client.post(
            reverse("comment_list"),
            {
                "project": f"{self.project.id}",
                "content": "this is content test",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_comment(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("comment_list"),
            {
                "project": f"{self.project.id}",
                "content": "this is content test",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_edit_own_comment(self):
        self.client.force_login(self.user)
        updated_content = "this is content test edited"
        response = self.client.put(
            reverse(
                "comment_detail",
                kwargs={"pk": self.comment_4_project_1_user_1.id},
            ),
            {"content": updated_content},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment = Comment.objects.get(id=self.comment_4_project_1_user_1.id)
        self.assertEqual(updated_content, comment.content)

    def test_edit_somebodies_else_comment(self):
        self.client.force_login(self.user_2)
        updated_content = "this is content test edited"
        response = self.client.put(
            reverse(
                "comment_detail",
                kwargs={"pk": self.comment_4_project_1_user_1.id},
            ),
            {"content": updated_content},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
