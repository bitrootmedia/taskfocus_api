from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Project, User, ProjectAccess, Task, TaskBlock


class TaskBlocksTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="user1")
        cls.user_2 = User.objects.create(username="user2")
        cls.user_3 = User.objects.create(username="user3")

        cls.task_1 = Task.objects.create(
            owner=cls.user, title="Task 1", description="Task 1 Description"
        )

        cls.block_1 = TaskBlock.objects.create(
            task=cls.task_1,
            block_type=TaskBlock.BlockTypeChoices.MARKDOWN,
            content="Block 1 Content",
            created_by=cls.user,
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

        cls.block_2 = TaskBlock.objects.create(
            task=cls.task_2,
            block_type=TaskBlock.BlockTypeChoices.MARKDOWN,
            content="Block 2 Content",
            created_by=cls.user_2,
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

        cls.block_3 = TaskBlock.objects.create(
            task=cls.task_3,
            block_type=TaskBlock.BlockTypeChoices.MARKDOWN,
            content="Block 3 Content",
            created_by=cls.user_3,
        )

        cls.block_4 = TaskBlock.objects.create(
            task=cls.task_3,
            block_type=TaskBlock.BlockTypeChoices.MARKDOWN,
            content="Block 3 Content",
            created_by=cls.user_3,
            position=1,
        )

        ProjectAccess.objects.create(project=cls.project_3, user=cls.user)

    def test_task_block_list_no_task_access(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(
            reverse("task_block_list", kwargs={"pk": str(self.task_1.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_block_list_authenticated_and_ordered(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("task_block_list", kwargs={"pk": str(self.task_3.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get("results")
        self.assertEqual(results[0].get("id"), str(self.block_3.id))
        self.assertEqual(results[1].get("id"), str(self.block_4.id))

    def test_task_block_create_no_task_access(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(
            reverse("task_block_list", kwargs={"pk": str(self.task_1.id)}),
            {
                "task": self.task_1.id,
                "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                "content": '{"markdown":"SHOULD NOT BE CREATED"}',
                "position": 1,
                "created_by": self.user_2.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_block_create_not_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_list", kwargs={"pk": self.task_3.id}),
            {
                "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                "content": '{"markdown":"NEW BLOCK CONTENT"}',
                "position": 3,
                "created_by": self.user.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_task_block_reorder_on_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_list", kwargs={"pk": self.task_1.id}),
            {
                "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                "content": '{"markdown":"NEW BLOCK CONTENT"}',
                "position": 0,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.block_1.refresh_from_db()
        # Existing block was 0, should be 1 now.
        self.assertEqual(self.block_1.position, 1)

    def test_task_block_update_no_access(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.put(
            reverse("task_block_detail", kwargs={"pk": self.block_1.id}),
            {"content": '{"markdown": "Will not be updated"}'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_block_update_not_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse("task_block_detail", kwargs={"pk": self.block_4.id}),
            {"content": '{"markdown": "Block 4 Updated Content"}'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.block_4.refresh_from_db()
        self.assertEqual(
            self.block_4.content, {"markdown": "Block 4 Updated Content"}
        )

    def test_task_block_reorder_on_update(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.put(
            reverse("task_block_detail", kwargs={"pk": self.block_4.id}),
            {"position": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.block_3.refresh_from_db()
        self.block_4.refresh_from_db()
        # was 1 should be 0
        self.assertEqual(self.block_4.position, 0)
        self.assertEqual(self.block_3.position, 1)

    def test_task_block_delete_no_access(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(
            reverse("task_block_detail", kwargs={"pk": self.block_1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_block_delete_not_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse("task_block_detail", kwargs={"pk": self.block_4.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_task_block_reorder_on_delete(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.delete(
            reverse("task_block_detail", kwargs={"pk": self.block_3.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.block_4.refresh_from_db()
        # was 1 should be 0
        self.assertEqual(self.block_4.position, 0)
