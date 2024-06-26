# Generated by Django 4.2.4 on 2023-10-25 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Customer', '0018_alter_property_tax_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='bulding_age',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('0-1', '0-1 Year'), ('2-5 ', '2-5 Year'), ('6-10', '6-10 Year'), ('11-15', '11-15 Year'), ('16-20', '16-20 Year'), ('21-30', '21-30 Year'), ('31-35', '31-35 Year'), ('36-40', '36-40 Year'), ('41-45', '41-45 Year'), ('45-50', '45-50 Year')], max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='garage',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')], max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='last_renovated',
            field=models.CharField(blank=True, choices=[('0-1', '0-1 Km'), ('2-5 ', '2-5 Km'), ('6-10', '6-10 Km'), ('11-15', '11-15 Km'), ('16-20', '16-20 Km'), ('21-30', '21-30 Km'), ('31-35', '31-35 Km'), ('36-40', '36-40 Km'), ('41-45', '41-45 Km'), ('45-50', '45-50 Km')], max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='major_road',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('0-1', '0-1'), ('2-5', '2-5'), ('6-10', '6-10'), ('11-15', '11-15'), ('16-20', '16-20')], max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='near_hospital',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('0-1', '0-1'), ('2-5', '2-5'), ('6-10', '6-10'), ('11-15', '11-15'), ('16-20', '16-20')], max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='near_supermarket',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('0-1', '0-1'), ('2-5', '2-5'), ('6-10', '6-10'), ('11-15', '11-15'), ('16-20', '16-20')], max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='rooms',
            field=models.CharField(blank=True, choices=[('', 'Select an option'), ('0', 'Ground'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'), ('25', '25'), ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30'), ('31', '31'), ('32', '32'), ('33', '33'), ('34', '34'), ('35', '35'), ('36', '36'), ('37', '37'), ('38', '38'), ('39', '39'), ('40', '40'), ('41', '41'), ('42', '42'), ('43', '43'), ('44', '44'), ('45', '45'), ('46', '46'), ('47', '47'), ('48', '48'), ('49', '49'), ('50', '50')], max_length=40, null=True),
        ),
    ]
