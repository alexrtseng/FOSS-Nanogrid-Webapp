from django.db import models


class SmartMeter(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    field_name = models.CharField(max_length=255, verbose_name="Field Name")

    distribution_board = models.CharField(
        max_length=255, verbose_name="Distribution Board"
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Longitude"
    )
    feeder_connection = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Feeder Connection"
    )
    feeder = models.CharField(max_length=255, verbose_name="Feeder")
    serial_no = models.CharField(max_length=255, verbose_name="Serial No.")
    modbus_port = models.PositiveIntegerField(verbose_name="Modbus Port")
    mac_address = models.CharField(
        max_length=17, verbose_name="MAC Address"
    )  # MAC address max length is 17
    comments = models.TextField(null=True, blank=True, verbose_name="Comments")
    username = models.CharField(max_length=255, verbose_name="Username")
    password = models.CharField(max_length=255, verbose_name="Password")
    secondary_id = models.PositiveSmallIntegerField(
        default=1, verbose_name="Secondary Id",
    )  # secondary used instead of slave


class ThirtyMinAvg(models.Model):
    smart_meter = models.ForeignKey(SmartMeter, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    active = models.FloatField(blank=True, null=True)
    reactive = models.FloatField(blank=True, null=True)
    apparent = models.FloatField(blank=True, null=True)
    power_factor = models.FloatField(blank=True, null=True)
    freq = models.FloatField(blank=True, null=True)
    humidity = models.FloatField(blank=True, null=True)
    temperature = models.FloatField(blank=True, null=True)
    irradiance = models.FloatField(blank=True, null=True)
    data_points = models.PositiveIntegerField(blank=False, null=False, default=0)

    def __str__(self):
        return f"30 Min Avg - {self.smart_meter.field_name} at {self.timestamp}"


class RealTimeMeter(models.Model):
    smart_meter = models.ForeignKey(SmartMeter, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    active = models.FloatField(blank=True, null=True)
    reactive = models.FloatField(blank=True, null=True)
    apparent = models.FloatField(blank=True, null=True)
    power_factor = models.FloatField(blank=True, null=True)
    freq = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Real Time - {self.smart_meter.field_name} at {self.timestamp}"
