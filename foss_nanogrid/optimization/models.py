from django.db import models

# Model for ESS sytems: Probably Batteries
class ESS(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=250)
    capacity = models.FloatField(verbose_name="Capacity") # in MWh
    max_power = models.FloatField(verbose_name="Max Power") # in MW
    efficiency = models.FloatField(verbose_name="Efficiency") # in percentage
    rte = models.FloatField(verbose_name="Round Trip Efficiency") # in percentage
    sd = models.FloatField(verbose_name="Self Discharge") # in percentage per hour
    dd = models.FloatField(verbose_name="Depth of Discharge") # in percentage
