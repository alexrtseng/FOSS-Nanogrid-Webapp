# Generated by Django 5.0.6 on 2024-07-01 13:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecasting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pvpanel',
            name='capacity',
            field=models.FloatField(default=1, verbose_name='Capacity'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('predicted_power', models.FloatField(verbose_name='Predicted Power')),
                ('actual_power', models.FloatField(blank=True, null=True, verbose_name='Actual Power')),
                ('model', models.CharField(max_length=100)),
                ('resolution', models.IntegerField(verbose_name='Resolution')),
                ('min_resolution', models.BooleanField(verbose_name='Minimum Resolution')),
                ('pv', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forecasting.pvpanel')),
            ],
        ),
    ]
