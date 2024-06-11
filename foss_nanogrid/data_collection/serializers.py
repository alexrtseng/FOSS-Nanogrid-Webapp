from rest_framework import serializers
from .models import *

class SmartMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartMeter
        exclude = []

class ThirtyMinAvgSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirtyMinAvg
        exclude = []

class RealTimeMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealTimeMeter
        exclude = []
    
    