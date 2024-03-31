# Generated by Django 4.2.4 on 2023-09-14 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FindMyNestApp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='features',
        ),
        migrations.AlterField(
            model_name='subscription',
            name='sub_type',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.DeleteModel(
            name='Feature',
        ),
        migrations.AddField(
            model_name='subscription',
            name='features',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
