# Generated by Django 5.0.6 on 2024-06-14 13:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_collection', '0004_smartmeter_connected'),
    ]

    operations = [
        migrations.RenameField(
            model_name='smartmeter',
            old_name='connected',
            new_name='recieving_info',
        ),
    ]
