# Generated by Django 4.2.7 on 2024-03-15 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0033_alter_property_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='user_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Customer'), (2, 'Admin'), (3, 'Agent'), (4, 'Executive'), (5, 'Editor')], default=1),
        ),
    ]
