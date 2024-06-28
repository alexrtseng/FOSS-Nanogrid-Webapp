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