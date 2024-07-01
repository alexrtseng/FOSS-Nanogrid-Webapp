import numpy as np
from django.test import TestCase
import pandas as pd
from .pv_forecasting.pv_forecasting_predict import PVPredict


# Create your tests here.
class ForecastingTestCase(TestCase):
    df = pd.read_csv('./forecasting/tests/data/forecast_pv_test_df.csv')
    df_features = df[
        ["min", "month", "dayofyear", "weekofyear", "quarter", "Tamb", "RH", "POA"]
    ].copy()
    correct_preds = df["Pac_pred"].values

    # Test the forecast_pv function
    def test_forecast_pv(self):
        pv_predictor = PVPredict()
        predictions = pv_predictor._forecast_pv(self.df_features)
        self.assertTrue(np.array_equal(self.correct_preds, predictions))
