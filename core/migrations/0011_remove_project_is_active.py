# Generated by Django 4.1.7 on 2023-04-18 16:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_task_urgency_level_alter_task_status"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="is_active",
        ),
    ]
