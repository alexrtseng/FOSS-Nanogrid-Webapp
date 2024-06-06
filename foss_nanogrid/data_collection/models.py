from unittest.util import _MAX_LENGTH
from django.db import models

class SmartMeters (models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    field_name = models.CharField(max_length=255, verbose_name="Field Name")
    
    distribution_board = models.CharField(max_length=255, verbose_name="Distribution Board")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Longitude")
    feeder_connection = models.CharField(max_length=255, null=True, blank=True, verbose_name="Feeder Connection")
    feeder = models.CharField(max_length=255, verbose_name="Feeder")
    serial_no = models.CharField(max_length=255, verbose_name="Serial No.")
    modbus_port = models.PositiveIntegerField(verbose_name="Modbus Port")
    mac_address = models.CharField(max_length=17, verbose_name="MAC Address")  # MAC address max length is 17
    installed = models.BooleanField(default=False, verbose_name="Installed?")
    comments = models.TextField(null=True, blank=True, verbose_name="Comments")
    username = models.CharField(max_length=255, verbose_name="Username")
    password = models.CharField(max_length=255, verbose_name="Password")
    secondary_id = models.BooleanField(default=False, verbose_name="Secondary Id") # secondary used instead of slave

