# Generated by Django 4.1.7 on 2023-04-18 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_alter_task_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="urgency_level",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CRITICAL", "CRITICAL"),
                    ("MAJOR", "MAJOR"),
                    ("MEDIUM", "MEDIUM"),
                    ("MINOR", "MINOR"),
                ],
                max_length=150,
                null=True,
            ),
        ),
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
                    ("ON_HOLD", "ON_HOLD"),
                ],
                max_length=150,
                null=True,
            ),
        ),
    ]