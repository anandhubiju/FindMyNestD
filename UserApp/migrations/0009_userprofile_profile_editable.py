# Generated by Django 4.2.7 on 2024-01-18 04:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserApp', '0008_agentprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='profile_editable',
            field=models.BooleanField(default=True),
        ),
    ]
