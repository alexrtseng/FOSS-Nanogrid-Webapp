"""
NOT IN USE 
Running these tasks asyncronously with a return value will add additional 
logic. Although this would be useful for high throughput requirements, 
it is overly complicated to implement for UCY.
"""

from decimal import Decimal
from celery import shared_task
import pandas as pd
import numpy as np
from .models import PVPanel, Prediction
from .pv_forecasting.pv_forecasting_predict import PVPredict
import logging
import json

log = logging.getLogger(__name__)


class PVForecastEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # or float(obj) for numerical context
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        return super().default(obj)


@shared_task
def forecast_pv_timestamp_range(
    predictor: PVPredict,
    start: pd.Timestamp,
    end: pd.Timestamp,
    pv: PVPanel,
    resolution: int = 30,
    min_resolution: bool = True,
    all_models: bool = True,
):
    return predictor.forecast_pv_timestamp_range(
        start, end, pv, resolution, min_resolution, all_models
    )


# Predict tomorrow's PV output and store it in the database
def _forecast_and_store_tomorrow_pvs():
    # Get all PV panels
    pvs = PVPanel.objects.all()
    # Create a predictor
    predictor = PVPredict()
    # Get tomorrow's date
    tomorrow = pd.Timestamp.now().date() + pd.Timedelta(days=1)
    # Get the start and end of tomorrow
    start = pd.Timestamp(tomorrow)
    end = pd.Timestamp(tomorrow) + pd.Timedelta(days=1)
    # Iterate over all PV panels
    for pv in pvs:
        # Forecast the PV output for tomorrow
        forecast = predictor.forecast_pv_timestamp_range(start, end, pv)
        # Store the forecast in the database
        forecast_dict = predictor.forecasted_power_to_dict(forecast, pv=pv)
        Prediction.objects.create(
            pv=pv,
            timestamp=pd.Timestamp.now(tz="UTC"),
            prediction_json=json.dumps(forecast_dict, cls=PVForecastEncoder),
        )


@shared_task
def forecast_and_store_tomorrow_pvs():
    _forecast_and_store_tomorrow_pvs()
    return True
