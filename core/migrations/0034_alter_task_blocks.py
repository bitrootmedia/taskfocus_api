# Generated by Django 4.1.7 on 2023-11-23 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_alter_task_blocks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='blocks',
            field=models.JSONField(default=list),
        ),
    ]
