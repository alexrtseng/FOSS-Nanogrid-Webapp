from turtle import st
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from data_collection.models import SmartMeter
from .helper_functions.net_load import preds_to_net_load_dict
from .helper_functions.views_helper import (
    start_end_time_valid,
    num_req_calls_valid,
    get_forecast_params,
)
from .load_forecasting.load_forecasting_predict import LoadPredict
from .pv_forecasting.pv_forecasting_predict import PVPredict
from .models import PVPanel
import pandas as pd
import logging
import math

log = logging.getLogger(__name__)


# Create your views here.
# Must request with paramgs start, end, and pv. Optional params are resolution, min_resolution, and all_models
@api_view(["GET"])
def forecast_pv(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")

    predictor = PVPredict()

    # Get query params
    if (
        not "start" in request.query_params
        or not "end" in request.query_params
        or not "pv" in request.query_params
    ):
        log.info("Invalid info/ request. Missing start or end query params")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    start, end, resolution, min_resolution = get_forecast_params(request)
    pv_name = request.query_params["pv"]
    if "all_models" in request.query_params:
        all_models = request.query_params["all_models"].lower() in [
            "true",
            "1",
            "t",
            "y",
            "yes",
        ]
    else:
        all_models = True

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

    if not start_end_time_valid(start, end):
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        start, end = start_end_time_valid(start, end)

    if not num_req_calls_valid(start, end, min_resolution):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # Run predictions
    predictions = predictor.forecast_pv_timestamp_range(
        start, end, pv, resolution, min_resolution, all_models
    )
    if not isinstance(predictions, pd.DataFrame):
        log.info("Failure in forecast_pv_timestamp_range")
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    predictions_json = PVPredict.forecasted_power_to_dict(predictions, pv=pv)
    return Response(predictions_json, status=status.HTTP_200_OK)


# Use forecasting model to forecast load for UCY Microgrid in param specified range
# Must request with params start, end. Optional params are resolution and min_resolution
@api_view(["GET"])
def forecast_ucy_load(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")

    predictor = LoadPredict()

    # Get query params
    if not "start" in request.query_params or not "end" in request.query_params:
        log.info("Invalid info/ request. Missing start or end query params")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    start, end, resolution, min_resolution = get_forecast_params(request)
    log.info(f"Forecasting load for {start} to {end}")

    # Prevent invalid input
    if not start_end_time_valid(start, end):
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        start, end = start_end_time_valid(start, end)

    if not num_req_calls_valid(start, end, min_resolution):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # Run predictions
    sm = SmartMeter.objects.get(field_name="EC_SM2")
    predictions = predictor.forecast_load_timestamp_range(
        start=start,
        end=end,
        sm=sm,
        resolution=resolution,
        min_resolution=min_resolution,
    )
    if not isinstance(predictions, pd.DataFrame):
        log.info("Failure in forecast_pv_timestamp_range")
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    predictions_json = LoadPredict.forecasted_power_to_dict(predictions)
    return Response(predictions_json, status=status.HTTP_200_OK)


# Use PV and load to forecast net load for UCY microgrid in param specified range
@api_view(["GET"])
def forecast_net_load(request):
    if not request.method == "GET":
        log.info("Invalid info/ request. {request.method} instead of GET")

    # Get query params
    if not "start" in request.query_params or not "end" in request.query_params:
        log.info("Invalid info/ request. Missing start or end query params")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    start, end, resolution, min_resolution = get_forecast_params(request)
    if "pv" in request.query_params:
        pv_name = request.query_params["pv"]
    else:
        pv_name = "future-ucy-pv"
    if "all_models" in request.query_params:
        all_models = request.query_params["all_models"].lower() in [
            "true",
            "1",
            "t",
            "y",
            "yes",
        ]
    else:
        all_models = True
    if "pv" in request.query_params:
        pv_name = request.query_params["pv"]
    else:
        pv_name = "future-ucy-pv"

    log.info(f"Forecasting net load for {start} to {end}")

    # Prevent invalid input
    try:
        pv = PVPanel.objects.get(name=pv_name)
    except PVPanel.DoesNotExist:
        log.info("Invalid info/ request. PV panel not found")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        log.info(f"Error in getting PV panel: {e}")
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not start_end_time_valid(start, end):
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        start, end = start_end_time_valid(start, end)

    if not num_req_calls_valid(start, end, min_resolution):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # Predict production and load
    pv_predictor = PVPredict()
    load_predictor = LoadPredict()
    pv_predictions = pv_predictor.forecast_pv_timestamp_range(
        start=start,
        end=end,
        pv=pv,
        resolution=resolution,
        min_resolution=min_resolution,
        all_models=all_models,
    )
    if not isinstance(pv_predictions, pd.DataFrame):
        log.info("Failure in forecast_pv_timestamp_range")
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    sm = SmartMeter.objects.get(field_name="EC_SM2")
    load_predictions = load_predictor.forecast_load_timestamp_range(
        start=start,
        end=end,
        sm=sm,
        resolution=resolution,
        min_resolution=min_resolution,
    )
    if not isinstance(load_predictions, pd.DataFrame):
        log.info("Failure in forecast_pv_timestamp_range")
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Calculate net load
    net_load = preds_to_net_load_dict(
        pv_predictions=pv_predictions,
        load_predictions=load_predictions,
        sm_name=sm.field_name,
        pv_name=pv_name,
        latitude=pv.latitude,
        longitude=pv.longitude
    )

    return Response(net_load, status=status.HTTP_200_OK)