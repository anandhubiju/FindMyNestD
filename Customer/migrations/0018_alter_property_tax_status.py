# Generated by Django 4.2.4 on 2023-10-24 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0017_property_bathrooms_attached'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='tax_status',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('Included', 'Included'), ('Not Included', 'Not Included')], max_length=40, null=True),
        ),
    ]
