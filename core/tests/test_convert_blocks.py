import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from core.models import User, Task, Project, TaskBlock


class ConvertBlocksTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "convert_blocks",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_convert_blocks(self):
        user = User.objects.create(username="user1")
        project = Project.objects.create(title="project1", owner=user)

        markdown_old_block = {"type": "markdown", "content": "mkd down\nwith\n\n**different**\n*stuff in it*\n##### test"}
        image_old_block = {"type": "image", "path": "some/path/here"}
        checklist_old_block = {
            "type": "checklist",
            "title": "the title",
            "elements": [
                {"label": "a", "checked": True},
                {"label": "b", "checked": False}
            ]
        }
        empty_checklist = {"type": "checklist", "title": "empty checklist", "elements": []}

        old_blocks_json = json.dumps(
            [markdown_old_block, image_old_block, checklist_old_block, empty_checklist]
        )

        task = Task.objects.create(
            owner=user,
            title="Task 1",
            description="Task Description",
            project=project,
            blocks_old=old_blocks_json,
        )

        out = self.call_command()
        self.assertIn(str(task.id), out)

        created_blocks = TaskBlock.objects.order_by("position")

        self.assertEqual(TaskBlock.objects.count(), created_blocks.count())
        self.assertEqual(created_blocks[0].block_type, TaskBlock.BlockTypeChoices.MARKDOWN)
        self.assertEqual(created_blocks[0].position, 0)
        self.assertEqual(created_blocks[0].content, json.dumps({
            "markdown": "mkd down\nwith\n\n**different**\n*stuff in it*\n##### test"
        }))
        self.assertEqual(created_blocks[1].block_type, TaskBlock.BlockTypeChoices.IMAGE)
        self.assertEqual(created_blocks[1].position, 1)
        self.assertEqual(created_blocks[1].content, json.dumps({"path":"some/path/here"}))
        self.assertEqual(created_blocks[2].block_type, TaskBlock.BlockTypeChoices.CHECKLIST)
        self.assertEqual(created_blocks[2].position, 2)
        self.assertEqual(created_blocks[2].content, json.dumps(
            {
                "title": "the title",
                "elements": [
                    {"label": "a", "checked": True},
                    {"label": "b", "checked": False}
                ]
            }
        ))
        self.assertEqual(created_blocks[3].block_type, TaskBlock.BlockTypeChoices.CHECKLIST)
        self.assertEqual(created_blocks[3].position, 3)
        self.assertEqual(created_blocks[3].content, json.dumps({
            "title": "empty checklist",
            "elements": []
        }))
