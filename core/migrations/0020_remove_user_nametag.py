# Generated by Django 4.1.7 on 2023-06-04 21:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_user_nametag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='nametag',
        ),
    ]
