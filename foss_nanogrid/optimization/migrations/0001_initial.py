# Generated by Django 5.0.6 on 2024-07-10 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ESS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=250)),
                ('capacity', models.FloatField(verbose_name='Capacity')),
                ('max_power', models.FloatField(verbose_name='Max Power')),
                ('efficiency', models.FloatField(verbose_name='Efficiency')),
                ('rte', models.FloatField(verbose_name='Round Trip Efficiency')),
                ('sd', models.FloatField(verbose_name='Self Discharge')),
                ('dd', models.FloatField(verbose_name='Depth of Discharge')),
            ],
        ),
    ]
