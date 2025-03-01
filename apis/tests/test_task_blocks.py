from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apis.serializers import TaskBlockWebsocketSerializer
from core.models import Project, User, ProjectAccess, Task, TaskBlock


class TaskBlocksTestsV2(APITestCase):
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
            content="Block 4 Content",
            created_by=cls.user_3,
            position=1,
        )

        cls.block_5 = TaskBlock.objects.create(
            task=cls.task_3,
            block_type=TaskBlock.BlockTypeChoices.MARKDOWN,
            content="Block 5 Content",
            created_by=cls.user_3,
            position=2,
        )

        ProjectAccess.objects.create(project=cls.project_3, user=cls.user)

        cls.task_4 = Task.objects.create(
            owner=cls.user,
            title="Task 4",
            description="Task 4 Description",
        )

    def test_task_block_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("task_block_list", kwargs={"task": str(self.task_3.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get("results")
        self.assertEqual(results[0].get("id"), str(self.block_3.id))
        self.assertEqual(results[1].get("id"), str(self.block_4.id))

    def test_task_block_list_task_doesnt_exist(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(
            reverse(
                "task_block_list",
                kwargs={
                    "task": str(  # random uuid
                        "0508f0aa-8cdd-4d63-b67f-ab2fcc90cb3f"
                    )
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_block_list_no_task_access(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(
            reverse("task_block_list", kwargs={"task": str(self.task_1.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_block_list_empty(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("task_block_list", kwargs={"task": str(self.task_4.id)})
        )
        results = response.json().get("results")
        self.assertEqual(len(results), 0)

    # Mock Pusher Websocket call
    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_create_no_move(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_create"),
            {
                "task": str(self.task_1.id),
                "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                "content": "New Block Content",
                "position": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_block = TaskBlock.objects.get(task=self.task_1.id, position=1)
        self.assertEqual(created_block.created_by, self.user)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_1.id}",
            event_name="block_created",
            data={
                "changed_positions": {},
                "created_block": TaskBlockWebsocketSerializer(
                    instance=created_block
                ).data,
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_create_with_move(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_create"),
            {
                "task": str(self.task_3.id),
                "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                "content": "New Block Content",
                "position": 0,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_block = TaskBlock.objects.get(task=self.task_3.id, position=0)
        self.assertEqual(created_block.created_by, self.user)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_3.id}",
            event_name="block_created",
            data={
                # Assure blocks moved
                "changed_positions": {
                    str(self.block_3.id): 1,
                    str(self.block_4.id): 2,
                    str(self.block_5.id): 3,
                },
                "created_block": TaskBlockWebsocketSerializer(
                    instance=created_block
                ).data,
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_create_with_move_in_the_middle(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_create"),
            {
                "task": str(self.task_3.id),
                "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                "content": "New Block Content",
                "position": 1,
            },
            format="json",
        )

        created_block = TaskBlock.objects.get(task=self.task_3.id, position=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_3.id}",
            event_name="block_created",
            data={
                # Assure blocks moved
                "changed_positions": {
                    str(self.block_4.id): 2,
                    str(self.block_5.id): 3,
                },
                "created_block": TaskBlockWebsocketSerializer(
                    instance=created_block
                ).data,
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_update(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse("task_block_update"),
            {
                "task": str(self.task_1.id),
                "block": str(self.block_1.id),
                "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                "content": "Block 1 Content UPDATED",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json().get("content"), "Block 1 Content UPDATED"
        )
        self.block_1.refresh_from_db()

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_1.id}",
            event_name="block_updated",
            data={
                "updated_block": TaskBlockWebsocketSerializer(
                    instance=self.block_1
                ).data
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_delete(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse("task_block_delete"),
            {
                "task": str(self.task_3.id),
                "block": str(self.block_3.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_3.id}",
            event_name="block_archived",
            data={
                "archived_block": str(self.block_3.id),
                "changed_positions": {
                    str(self.block_4.id): 0,
                    str(self.block_5.id): 1,
                },
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_move_up(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_move"),
            {
                "task": str(self.task_3.id),
                "block": str(self.block_3.id),
                "position": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_3.id}",
            event_name="block_moved",
            data={
                "changed_positions": {
                    str(self.block_4.id): 0,
                    str(self.block_5.id): 1,
                    str(self.block_3.id): 2,
                }
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_move_up_over_top_position(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_move"),
            {
                "task": str(self.task_3.id),
                "block": str(self.block_3.id),
                "position": 25,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_3.id}",
            event_name="block_moved",
            data={
                "changed_positions": {
                    str(self.block_4.id): 0,
                    str(self.block_5.id): 1,
                    str(self.block_3.id): 2,
                }
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_move_down(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_move"),
            {
                "task": str(self.task_3.id),
                "block": str(self.block_5.id),
                "position": 0,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_3.id}",
            event_name="block_moved",
            data={
                "changed_positions": {
                    str(self.block_5.id): 0,
                    str(self.block_3.id): 1,
                    str(self.block_4.id): 2,
                }
            },
        )

    @patch("core.utils.websockets.WebsocketHelper.send")
    def test_block_move_down_below_zero(self, mock_websocket_send):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("task_block_move"),
            {
                "task": str(self.task_3.id),
                "block": str(self.block_5.id),
                "position": -25,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_websocket_send.assert_called_once_with(
            channel=f"{self.task_3.id}",
            event_name="block_moved",
            data={
                "changed_positions": {
                    str(self.block_5.id): 0,
                    str(self.block_3.id): 1,
                    str(self.block_4.id): 2,
                }
            },
        )
