# Generated by Django 4.1.7 on 2023-04-05 09:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_alter_task_status_alter_taskworksession_stopped_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taskworksession",
            name="message",
            field=models.TextField(blank=True, null=True),
        ),
    ]
