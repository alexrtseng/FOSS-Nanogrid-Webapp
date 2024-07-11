from django.db import models

# Model for ESS sytems: Probably Batteries
class ESS(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=250)
    capacity = models.FloatField(verbose_name="Capacity") # in MWh
    max_charge = models.FloatField(verbose_name="Max Power") # in MW
    max_discharge = models.FloatField(verbose_name="Max Discharge Power") # in MW
    charge_efficiency = models.FloatField(verbose_name="Charge Efficiency") # in percentage
    discharge_efficiency = models.FloatField(verbose_name="Discharge Efficiency") # in percentage
    self_discharge = models.FloatField(verbose_name="Self Discharge") # in percentage per hour
    depth_of_discharge = models.FloatField(verbose_name="Depth of Discharge") # in percentage
    pref_max_soc = models.FloatField(verbose_name="Preferred Max SOC") # in percentage
    pref_min_soc = models.FloatField(verbose_name="Preferred Min SOC") # in percentage
