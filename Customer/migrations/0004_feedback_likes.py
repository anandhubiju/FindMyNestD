# Generated by Django 4.2.4 on 2023-09-21 10:17

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Customer', '0003_alter_feedback_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_feedbacks', to=settings.AUTH_USER_MODEL),
        ),
    ]
