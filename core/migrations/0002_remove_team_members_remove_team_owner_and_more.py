# Generated by Django 4.1.4 on 2022-12-21 22:14

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="team",
            name="members",
        ),
        migrations.RemoveField(
            model_name="team",
            name="owner",
        ),
        migrations.RemoveConstraint(
            model_name="projectaccess",
            name="core_project_access_unique_project_team",
        ),
        migrations.RemoveConstraint(
            model_name="taskaccess",
            name="core_task_access_unique_task_team",
        ),
        migrations.RemoveField(
            model_name="projectaccess",
            name="team",
        ),
        migrations.RemoveField(
            model_name="taskaccess",
            name="team",
        ),
        migrations.DeleteModel(
            name="Team",
        ),
    ]
