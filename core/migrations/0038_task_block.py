# Generated by Django 4.1.7 on 2024-07-14 21:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_pin'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='blocks',
            new_name='blocks_old',
        ),
        migrations.CreateModel(
            name='TaskBlock',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('block_type', models.CharField(choices=[('MARKDOWN', 'Markdown'), ('IMAGE', 'Image'), ('CHECKLIST', 'Checklist')], max_length=150)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('content', models.JSONField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='core.task')),
            ],
        ),
    ]