# Generated by Django 4.2.4 on 2023-09-22 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0004_feedback_likes'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
