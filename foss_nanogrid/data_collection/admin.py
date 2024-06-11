from django.contrib import admin
from .models import *

admin.site.register(SmartMeter)
admin.site.register(RealTimeMeter)
admin.site.register(ThirtyMinAvg)