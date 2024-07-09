import numpy as np
import pandas as pd
import xgboost as xgb
import logging
import environ
from ..helper_functions.calc_poa import calculate_poa_irradiance
from ..helper_functions.weather_api import get_weather_data_batch
from ..models import PVPanel
log = logging.getLogger(__name__)

"""
List of weights for model decision averaging based on accuracy
calculated in model training; index 1 is best singular model
but avg. prevents overfitting while improving accuracy
"""
MODEL_ACC_WEIGHTS = np.array([
    160.71058409,
    178.80454954,
    121.02804917,
    120.35546842,
    131.01931725,
    135.04967787,
])

# Number of models used in the ensemble; each has a file
NUM_OF_MODELS = 6

# Number of features for the model
NUM_OF_FEATURES = 8

"""
Models have been trained seperately using XGBoost with featurs: 
['min', 'month', 'dayofyear', 'weekofyear', 'quarter', 'Tamb', 'RH', 'POA']
and params: {
objective='reg:squarederror',
eval_metric='rmse',
early_stopping_rounds=50
}
This was the best model out of LSTM, LSTM + FNN, and hyperparameter tuned 
XGBoost models. Models trained/tested on UCYdemo data from 2019-2023 and cross validated
with 6 folds for a MAPE of ~1.43% (weighted avg. of 6 models).
Model files have been saved in native XGBoost binary format in the pv_models folder. 
Naming convention should follow: 'xgboost_pv_model_{#}.bin' with # indexing from 0
Takes local time and works in local time
"""

class PVPredict():
    # Contructor
    def __init__(self):
        self.regs = self._load_models()

    def __bool__(self):
        return True

    # Load the models from files
    def _load_models(self) -> list:
        regs = []
        for i in range(NUM_OF_MODELS):
            reg = xgb.XGBRegressor()
            reg.load_model(f"forecasting/pv_forecasting/pv_models_v1/xgboost_pv_model_{i}.bin")
            regs.append(reg)
        return regs
    
    # Return dataframe with weather features and datetime column given a time range and resolution
    def _get_weather_features(self, start: pd.Timestamp, end: pd.Timestamp, resolution, min_resolution: bool, pv: PVPanel) -> pd.DataFrame:
        # Get weather data from API
        response_data = get_weather_data_batch(start=start, end=end, longitude=pv.longitude, latitude=pv.latitude, resolution=resolution, min_resolution=min_resolution)

        # Create dataframe from API batched responses
        datetime = []
        tamb_series = []
        rh_series = []
        poa_series = []
        for individual_response in response_data['response']['responses']:
            if individual_response['success'] == True:
                for period in individual_response['response'][0]['periods']:
                    tamb_series.append(period['tempC'])
                    rh_series.append(period['humidity'])
                    poa_series.append(calculate_poa_irradiance(
                        solar_zenith=period['solrad']['zenithDEG'],
                        ghi=period['solrad']['ghiWM2'],
                        inclination=pv.inclination,
                        solar_azimuth=period['solrad']['azimuthDEG'],
                        site_azimuth=pv.azimuth
                        ))
                    datetime.append(period['dateTimeISO'])    # ALTERNATIVE IS ValidTime?
                    
            else:
                log.error(
                    f"Error in individual response for {pv.name}, Recieved error: {individual_response['error']}"
                )

        df = pd.DataFrame({
            'datetime': datetime,
            'Tamb': tamb_series,
            'RH': rh_series,
            'POA': poa_series
        })
        df['datetime'] = (pd
                          .to_datetime(df['datetime'])
                          .dt.tz_localize(None)
                        )

        return df

    # Create time features from a dataframe with a datetime column
    def _create_time_features(self, _df) -> pd.DataFrame:
        df = _df.copy()
        assert 'datetime' in df.columns, "Input dataframe must have a 'datetime' column"

        df['min'] = df['datetime'].dt.hour * 60 + df['datetime'].dt.minute
        df['quarter'] = df['datetime'].dt.quarter
        df['month'] = df['datetime'].dt.month
        df['dayofyear'] = df['datetime'].dt.dayofyear
        df['weekofyear'] = df['datetime'].dt.isocalendar().week

        return df[['min','month',
            'dayofyear','weekofyear', 'quarter', 'Tamb', 'RH', 'POA']]
    


    # Helper function to forecast PV power generation using pre-trained regression models
    # Input: model input features and a boolean all_models to use all models or just the best
    def _forecast_pv(self, input_features: pd.DataFrame, all_models: bool) -> np.array:
        # Check input features
        assert (
            input_features.shape[1] == NUM_OF_FEATURES
        ), f"Input features must have {NUM_OF_FEATURES} columns"

        if not all_models:
            return self.regs[1].predict(input_features)
        else:
            sum = np.zeros(input_features.shape[0])
            for i, reg in enumerate(self.regs):
                sum += MODEL_ACC_WEIGHTS[i] * reg.predict(input_features)
            
            return sum / np.sum(MODEL_ACC_WEIGHTS)

    # Forecast PV Power Output for range between start and end with minute resolution of resolution
    def forecast_pv_timestamp_range(self, start: pd.Timestamp, end: pd.Timestamp, pv: PVPanel, resolution: int=30, min_resolution: bool=True, all_models: bool=True, capacity=1.0) -> pd.DataFrame:
        # Check legitimate input
        assert start < end, "Start must be before end"
        
        # Create a dataframe of features
        df_features = self._get_weather_features(start, end, resolution, min_resolution, pv)
        if not isinstance(df_features, pd.DataFrame):
            return False
        
        datetime_col = df_features['datetime']
        df_features = self._create_time_features(df_features)

        # Forecast the PV power output
        predictions = self._forecast_pv(df_features, all_models)
        predictions = predictions * capacity
        return pd.DataFrame({
            'datetime': datetime_col,
            'Pac_pred': predictions
        })
    
    # Take predictions data from (columns: datetime, Pac_pred) and creates json file in SolarCast format
    # **kwargs: pv - PVPanel object, date_run - date the forecast model was run
    @staticmethod
    def forecasted_power_to_dict(_predictions: pd.DataFrame, model='XGBoost_pv_v1_all_models', **kwargs) -> dict:
        predictions = _predictions.sort_values(by='datetime').copy()
        values = []
        for index, row in predictions.iterrows():
            values.append({
                'Timestamp': row['datetime'],
                'kW': row['Pac_pred']
            })

        if 'pv' in kwargs and len(values) >= 1:
            forecast_dict = {
                'pv': kwargs['pv'].name,
                'latitude': kwargs['pv'].latitude,
                'longitude': kwargs['pv'].longitude,
                'capacity': kwargs['pv'].capacity,
                'unit': 'kW',
                'model': model,
                'date_run' : pd.Timestamp.now(tz='Asia/Nicosia') if 'date_run' not in kwargs else kwargs['date_run'],
                'forecasted_dates' : f"{values[0]['Timestamp']} to {values[-1]['Timestamp']}",
                'values': values
            }
        else:
            forecast_dict = {
                'values': values
            }

        return forecast_dict
        
        

        