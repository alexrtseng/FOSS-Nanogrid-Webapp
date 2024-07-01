from celery import shared_task
import pandas as pd
import numpy as np
from .models import PVPanel
from .pv_forecasting.pv_forecasting_predict import PVPredict
import logging

log = logging.getLogger(__name__)


@shared_task
def forecast_pv_timestamp_range(self, predictor: PVPredict, start: pd.Timestamp, end: pd.Timestamp, pv: PVPanel, resolution: int=30, min_resolution: bool=True, all_models: bool=True):
    return predictor.forecast_pv_timestamp_range(start, end, pv, resolution, min_resolution, all_models)