# Generated by Django 4.1.7 on 2023-04-05 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_alter_task_progress"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("TODO", "TODO"),
                    ("IN PROGRESS", "IN PROGRESS"),
                    ("BLOCKER", "BLOCKER"),
                    ("TO VERIFY", "TO VERIFY"),
                    ("DONE", "DONE"),
                ],
                max_length=150,
            ),
        ),
        migrations.AlterField(
            model_name="taskworksession",
            name="stopped_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]