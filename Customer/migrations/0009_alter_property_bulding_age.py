# Generated by Django 4.2.4 on 2023-10-09 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0008_alter_property_major_road_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='bulding_age',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('0-1', '0-1'), ('2-5 ', '2-5'), ('6-10', '6-10'), ('11-15', '11-15'), ('16-20', '16-20'), ('More than 10 Years', 'More than 10 Years')], max_length=40, null=True),
        ),
    ]
