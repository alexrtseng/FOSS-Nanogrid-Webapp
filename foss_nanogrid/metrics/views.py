from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import logging

from data_collection.models import SmartMeter, RealTimeMeter
log = logging.getLogger(__name__)

# Overview of metrics
@api_view(["GET"])
def devices(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    smart_meters = SmartMeter.objects.all()
    sm_dicts = list(map(lambda sm: {
        "name": sm.field_name,
        "ipAddress": sm.ip_address,
        "connectivityPercentage": 50,    # Still need to implement functionality on this
        "latitude": sm.latitude,
        "longitude": sm.longitude,
    }, smart_meters))

    return Response(sm_dicts, status=status.HTTP_200_OK)

    
def _create_rt_data_dict(sm):
    try:
        last_data_point = RealTimeMeter.objects.filter(smart_meter=sm).latest('timestamp')
        return {
            "name": sm.field_name,
            "recievingInfo": sm.recieving_info,
            "active": last_data_point.active,
            "reactive": last_data_point.reactive,
            "apparent": last_data_point.apparent,
            "frequency": last_data_point.freq,
            "powerFactor": last_data_point.power_factor,
        }
    except RealTimeMeter.DoesNotExist:
        return {
            "name": sm.field_name,
            "recievingInfo": False,
            "active": 0,
            "reactive": 0,
            "apparent": 0,
            "frequency": 0,
            "powerFactor": 0,
        }    


@api_view(["GET"])
def rt_all_meters(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    smart_meters = SmartMeter.objects.all()
    rt_data_dicts = list(map(_create_rt_data_dict, smart_meters))

    return Response(rt_data_dicts, status=status.HTTP_200_OK)