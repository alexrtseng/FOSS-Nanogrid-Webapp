# Generated by Django 5.0.6 on 2024-06-13 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_collection', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='thirtyminavg',
            old_name='irradiance',
            new_name='ghi_Wm2',
        ),
        migrations.RenameField(
            model_name='thirtyminavg',
            old_name='temperature',
            new_name='temp_C',
        ),
        migrations.AddField(
            model_name='thirtyminavg',
            name='dewpoint_C',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='thirtyminavg',
            name='feels_like_C',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='thirtyminavg',
            name='precip_mm',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='thirtyminavg',
            name='sky',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='thirtyminavg',
            name='visibility_km',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='thirtyminavg',
            name='wind_dir_deg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='thirtyminavg',
            name='wind_speed_kph',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
