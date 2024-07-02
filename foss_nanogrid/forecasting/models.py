from django.db import models

# Create your models here.
class PVPanel(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Longitude"
    )
    inclination = models.FloatField(verbose_name="Inclination")
    azimuth = models.FloatField(verbose_name="Azimuth")
    capacity = models.FloatField(verbose_name="Capacity")

class Prediction(models.Model):
    pv = models.ForeignKey(PVPanel, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    prediction_json = models.JSONField()