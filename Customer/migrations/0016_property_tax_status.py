# Generated by Django 4.2.4 on 2023-10-24 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0015_property_days_to_sell_property_property_tips_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='tax_status',
            field=models.BooleanField(default=True),
        ),
    ]