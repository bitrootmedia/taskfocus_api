import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Task, TaskBlock, User, Log


class Command(BaseCommand):
    help = 'Converts all existing blocks to new model based format'

    def handle(self, *args, **options):

        # Not ideal but we need a user to create a log.
        admin_user = User.objects.filter(is_superuser=True).first()

        for task in Task.objects.all():
            if task.blocks_old:
                blocks = []

                try:
                    old_blocks_dict = task.blocks_old
                    if isinstance(old_blocks_dict, str):  # we got un-serialized json
                        old_blocks_dict = json.loads(old_blocks_dict)

                    for i, block_data in enumerate(old_blocks_dict):
                        block_type = block_data.get("type")

                        if block_type == "markdown":
                            new_block = TaskBlock(
                                task=task,
                                block_type=TaskBlock.BlockTypeChoices.MARKDOWN,
                                content=json.dumps({"markdown": block_data.get("content")}),
                                position=i,
                                created_by=task.owner,
                            )
                        elif block_type == "image":
                            new_block = TaskBlock(
                                task=task,
                                block_type=TaskBlock.BlockTypeChoices.IMAGE,
                                content=json.dumps({"path": block_data.get("path")}),
                                position=i,
                                created_by=task.owner
                            )
                        elif block_type == "checklist":
                            new_block = TaskBlock(
                                task=task,
                                block_type=TaskBlock.BlockTypeChoices.CHECKLIST,
                                content=json.dumps(
                                    {
                                        "title": block_data.get("title"),
                                        "elements": block_data.get("elements")
                                    }
                                ),
                                position=i,
                                created_by=task.owner
                            )
                        else:
                            raise CommandError(
                                f"Block from task: {task.id} has invalid or no type (value: {block_type})"
                            )

                        blocks.append(new_block)

                    with transaction.atomic():
                        TaskBlock.objects.bulk_create(blocks)
                        self.stdout.write(
                            self.style.SUCCESS(f"Successfully converted {len(blocks)} blocks for task {task.id}"))

                except Exception as e:
                    Log.objects.create(
                        task=task,
                        created_by=admin_user,
                        message=f"Error while converting block(s) e: {str(e)}"
                    )
                    self.stdout.write(
                        self.style.ERROR(f"Something went wrong while converting task ({task.id}) blocks: {str(e)}"))
