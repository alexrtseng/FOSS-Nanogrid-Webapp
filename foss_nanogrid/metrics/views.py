from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import logging
log = logging.getLogger(__name__)

# Overview of metrics
@api_view(["GET"])
def index(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    
    

@api_view(["GET"])
def rt_meters(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    return render(request, "metrics/rt_meters.html")