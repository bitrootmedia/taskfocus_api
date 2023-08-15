# Generated by Django 4.1.7 on 2023-08-09 14:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0026_user_teams"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="progress",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="project",
            name="tag",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("OPEN", "OPEN"),
                    ("IN PROGRESS", "IN PROGRESS"),
                    ("BLOCKER", "BLOCKER"),
                    ("TO VERIFY", "TO VERIFY"),
                    ("DONE", "DONE"),
                    ("ON HOLD", "ON HOLD"),
                    ("IDEA", "IDEA"),
                ],
                max_length=150,
                null=True,
            ),
        ),
    ]
