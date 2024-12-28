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

        cls.task_4 = Task.objects.create(
            owner=cls.user,
            title="Task 4",
            description="Task 4 Description",
        )

    def test_task_block_list_no_task_access(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(
            reverse("task_block_list", kwargs={"task_id": str(self.task_1.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_block_list_ordered(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("task_block_list", kwargs={"task_id": str(self.task_3.id)})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get("results")
        self.assertEqual(results[0].get("id"), str(self.block_3.id))
        self.assertEqual(results[1].get("id"), str(self.block_4.id))

    def test_block_list_empty(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("task_block_list", kwargs={"task_id": str(self.task_4.id)})
        )
        results = response.json().get("results")
        self.assertEqual(len(results), 0)

    def test_block_list_reorder(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_3.id)}
            ),
            data=[
                {
                    "id": self.block_3.id,
                    "block_type": self.block_3.block_type,
                    "position": 1,
                },
                {
                    "id": self.block_4.id,
                    "block_type": self.block_4.block_type,
                    "position": 0,
                },
            ],
            format="json",
        )
        print(response.json())
        results = response.json().get("results")
        task_blocks = self.task_3.blocks.order_by("position")

        self.assertEqual(
            task_blocks.count(), 2
        )  # make sure block_4 was deleted
        self.assertEqual(results[0].get("id"), str(self.block_4.id))
        self.assertEqual(results[0].get("content"), self.block_4.content)
        self.assertEqual(results[1].get("id"), str(self.block_3.id))
        self.assertEqual(results[1].get("content"), self.block_3.content)

    def test_block_list_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_4.id)}
            ),
            data=[
                {
                    "id": None,
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 0,
                    "content": "New Block Content Here",
                },
                {
                    "id": None,
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 1,
                    "content": "Other block",
                },
            ],
            format="json",
        )
        results = response.json()["results"]
        task_blocks = self.task_4.blocks.all()
        self.assertEqual(task_blocks.count(), 2)
        self.assertEqual(results[0].get("content"), "New Block Content Here")

    def test_block_list_create_reorder(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_1.id)}
            ),
            data=[
                {
                    "id": None,
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 0,
                    "content": "New Block Content Here",
                },
                {
                    "id": self.block_1.id,
                    "block_type": self.block_1.block_type,
                    "position": 1,
                    "content": self.block_1.content,
                },
            ],
            format="json",
        )
        results = response.json().get("results")
        task_blocks = self.task_1.blocks.all().order_by("position")
        self.assertEqual(task_blocks.count(), 2)
        self.assertEqual(results[0].get("content"), "New Block Content Here")
        self.assertEqual(results[1].get("content"), self.block_1.content)

    def test_block_list_update(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_1.id)}
            ),
            data=[
                {
                    "id": self.block_1.id,
                    "block_type": self.block_1.block_type,
                    "position": self.block_1.position,
                    "content": self.block_1.content,
                },
                {
                    "id": None,
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 1,
                    "content": "Other block",
                },
            ],
            format="json",
        )

        results = response.json().get("results")

        task_blocks = self.task_1.blocks.all()

        self.assertEqual(task_blocks.count(), 2)
        self.assertEqual(results[0].get("id"), str(self.block_1.id))
        self.assertEqual(results[0].get("content"), self.block_1.content)
        self.assertEqual(results[1].get("content"), "Other block")

    def test_block_list_update_reorder(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_3.id)}
            ),
            data=[
                {
                    "id": self.block_4.id,
                    "block_type": self.block_4.block_type,
                    "position": 0,
                    "content": self.block_4.content,
                },
                {
                    "id": self.block_3.id,
                    "block_type": self.block_3.block_type,
                    "position": 1,
                    "content": self.block_3.content,
                },
            ],
            format="json",
        )

        results = response.json().get("results")
        task_blocks = self.task_3.blocks.order_by("position")

        self.assertEqual(task_blocks.count(), 2)
        self.assertEqual(results[0].get("id"), str(self.block_4.id))
        self.assertEqual(results[0].get("content"), self.block_4.content)
        self.assertEqual(results[1].get("id"), str(self.block_3.id))
        self.assertEqual(results[1].get("content"), self.block_3.content)

    def test_block_list_create_and_update(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_3.id)}
            ),
            data=[
                {
                    "id": None,
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 0,
                    "content": "# some content",
                },
                {
                    "id": self.block_4.id,
                    "block_type": self.block_4.block_type,
                    "position": 1,
                    "content": self.block_4.content,
                },
            ],
            format="json",
        )

        results = response.json().get("results")
        task_blocks = self.task_3.blocks.order_by("position")

        self.assertEqual(task_blocks.count(), 2)
        self.assertEqual(results[0].get("content"), "# some content")
        self.assertEqual(results[1].get("id"), str(self.block_4.id))
        self.assertEqual(results[1].get("content"), self.block_4.content)

    def test_block_list_delete_empty_post(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_1.id)}
            ),
            data=[],  # empty data to remove all blocks
            format="json",
        )

        task_blocks_count = self.task_1.blocks.order_by("position").count()
        self.assertEqual(task_blocks_count, 0)

    def test_block_list_delete_keep_other_blocks(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_3.id)}
            ),
            data=[
                # Keep block_4 data out of POST
                {
                    "id": self.block_3.id,
                    "block_type": self.block_3.block_type,
                    "position": 1,
                    "content": self.block_3.content,
                },
            ],
            format="json",
        )

        results = response.json().get("results")
        task_blocks = self.task_3.blocks.order_by("position")

        self.assertEqual(
            task_blocks.count(), 1
        )  # make sure block_4 was deleted
        self.assertEqual(results[0].get("id"), str(self.block_3.id))
        self.assertEqual(results[0].get("content"), self.block_3.content)

    def test_block_list_delete_and_create(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_3.id)}
            ),
            data=[
                # Keep block_4 data out of POST
                {
                    "id": self.block_3.id,
                    "block_type": self.block_3.block_type,
                    "position": 1,
                    "content": self.block_3.content,
                },
                {
                    "id": None,
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 0,
                    "content": "# some content",
                },
            ],
            format="json",
        )

        results = response.json().get("results")
        task_blocks = self.task_3.blocks.order_by("position")

        self.assertEqual(
            task_blocks.count(), 2
        )  # make sure block_4 was deleted
        self.assertEqual(results[0].get("content"), "# some content")
        self.assertEqual(results[1].get("id"), str(self.block_3.id))
        self.assertEqual(results[1].get("content"), self.block_3.content)

    def test_block_list_delete_create_and_update(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_3.id)}
            ),
            data=[
                # Keep block_4 data out of POST
                {
                    "id": self.block_3.id,
                    "block_type": self.block_3.block_type,
                    "position": 1,
                    "content": "New Content",
                },
                {
                    "id": None,  # Create new block
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 0,
                    "content": "# some content",
                },
            ],
            format="json",
        )

        results = response.json().get("results")
        task_blocks = self.task_3.blocks.order_by("position")

        self.assertEqual(
            task_blocks.count(), 2
        )  # make sure block_4 was deleted
        self.assertEqual(results[0].get("content"), "# some content")
        self.assertEqual(results[1].get("id"), str(self.block_3.id))
        self.assertEqual(results[1].get("content"), "New Content")

    def test_block_create_invalid_position(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_4.id)}
            ),
            data=[
                {
                    "id": None,  # new block,
                    "block_type": TaskBlock.BlockTypeChoices.CHECKLIST,
                    "position": 0,  # Invalid position
                    "content": "# some content",
                },
                {
                    "id": None,  # new block,
                    "block_type": TaskBlock.BlockTypeChoices.CHECKLIST,
                    "position": -1,  # Invalid position
                    "content": "# some content",
                },
            ],
            format="json",
        )

        existing_blocks = TaskBlock.objects.filter(task=self.task_4.id)

        self.assertEqual(len(existing_blocks), 0)

    def test_block_update_partial_invalid(self):
        # Nothing will be created if even one block is invalid

        self.client.force_authenticate(user=self.user_2)
        self.client.post(
            reverse(
                "task_block_list", kwargs={"task_id": str(self.task_2.id)}
            ),
            data=[
                {
                    "id": self.block_2.id,
                    "block_type": self.block_2.block_type,
                    "position": 1,
                    "content": None,  # Invalid content
                },
                {
                    "id": None,  # new block,
                    "block_type": TaskBlock.BlockTypeChoices.MARKDOWN,
                    "position": 2,
                    "content": "# some content",
                },
            ],
            format="json",
        )

        existing_blocks = TaskBlock.objects.filter(task=self.task_2.id)

        self.assertEqual(len(existing_blocks), 1)  # Nothing was created
        self.assertEqual(  # Nothing was updated
            existing_blocks[0].content, "Block 2 Content"
        )
