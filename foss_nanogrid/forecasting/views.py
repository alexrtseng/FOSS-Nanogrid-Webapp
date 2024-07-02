from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .pv_forecasting.pv_forecasting_predict import PVPredict
from .models import PVPanel
import pandas as pd
import logging
import math

log = logging.getLogger(__name__)

# Create your views here.
@api_view(["GET"])
def forecast_pv(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")
    
    predictor = PVPredict() 

    # Get query params
    if not "start" in request.query_params or not "end" in request.query_params or not "pv" in request.query_params:
        log.info("Invalid info/ request. Missing start or end query params")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    start = request.query_params["start"]
    end = request.query_params["end"]
    pv_name = request.query_params["pv"]
    if "resolution" in request.query_params:
        resolution = request.query_params["resolution"]
    else: 
        resolution = 30
    if "min_resolution" in request.query_params:
        min_resolution = request.query_params["min_resolution"].lower() in ['true', '1', 't', 'y', 'yes']
    else: 
        min_resolution = True
    if "all_models" in request.query_params:
        all_models = request.query_params["all_models"].lower() in ['true', '1', 't', 'y', 'yes']
    else: 
        all_models = True
    capacity = 1 if "capacity" not in request.query_params else float(request.query_params["capacity"]) # Default to 1 kW
    log.info(f"Forecasting for {start} to {end} on {pv_name}")
    
    # Prevent invalid input
    try:
        pv = PVPanel.objects.get(name=pv_name)
    except PVPanel.DoesNotExist:
        log.info("Invalid info/ request. PV panel not found")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        log.info(f"Error in getting PV panel: {e}")
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        assert start < end, "Start must be before end"
        assert start > pd.Timestamp.now(), "Start must be in the future"
        assert end < pd.Timestamp.now() + pd.Timedelta(days=15), "End must be within 15 days of now"
    except Exception as e:
        log.info(f"Invalid start or end timestamps: {e}")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    num_required_calls = math.ceil(((end - start).seconds / 3600) + (end - start).days * 24) if min_resolution else (end - start).days + 1
    if num_required_calls <= 0:
        log.info("Invalid info/ request. Start and end are too close")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    elif num_required_calls > 31:
        log.info("Invalid info/ request. Range too large of resolution; cannot batch API calls")
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # Run predictions
    predictions = predictor.forecast_pv_timestamp_range(start, end, pv, resolution, min_resolution, all_models, capacity)
    if not isinstance(predictions, pd.DataFrame):
        log.info("Failure in forecast_pv_timestamp_range")
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    predictions_json = PVPredict.forecasted_power_to_dict(predictions, pv=pv)
    return Response(predictions_json, status=status.HTTP_200_OK)
    

    
