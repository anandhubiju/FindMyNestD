# Generated by Django 4.2.4 on 2023-10-11 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0013_alter_property_bulding_age_alter_property_floor_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='property_type',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('House', 'Houses'), ('Apartment', 'Apartment'), ('Villa', 'Villas'), ('Commercial', 'Commercial'), ('Garage', 'Garage')], max_length=40, null=True),
        ),
    ]
