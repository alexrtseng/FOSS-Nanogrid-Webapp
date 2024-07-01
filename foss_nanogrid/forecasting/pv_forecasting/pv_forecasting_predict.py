import numpy as np
import pandas as pd
import xgboost as xgb
import math
import requests
import logging
import environ
from ..models import PVPanel
log = logging.getLogger(__name__)

env = environ.Env()
environ.Env.read_env(env_file='././foss_nanogrid/.env')
XWEATHER_CLIENT_ID = env("XWEATHER_CLIENT_ID")
XWEATHER_CLIENT_SECRET = env("XWEATHER_CLIENT_SECRET")
XWEATHER_BASE_URL = "https://api.aerisapi.com/"  # Different from one in data_collection (for batch feature)

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
"""
# Calculate the POA from the GHI
def calculate_poa_irradiance(solar_zenith, ghi, inclination, solar_azimuth, site_azimuth):
    elevation = 90 - solar_zenith

    sincident = ghi / np.sin(np.radians(elevation))

    if sincident < 0:
        sincident = 0

    poa = sincident * (np.cos(np.radians(elevation)) * np.sin(np.radians(inclination)) * np.cos(np.radians(site_azimuth - solar_azimuth)) + np.sin(np.radians(elevation)) * np.cos(np.radians(inclination)))

    if poa < 0:
        poa = 0
    
    return poa

class PVPredict():
    # Contructor
    def __init__(self):
        self.regs = self._load_models()

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
        # Make batch (requests) param for API call (signifigantly reduces number of calls to API)
        num_required_calls = math.ceil(((end - start).seconds / 3600) + (end - start).days * 24) if min_resolution else (end - start).days + 1
        assert num_required_calls <= 31, "Number of requests must be under 31"
        log.debug(f'Num of calls in batch: {num_required_calls}')
        batch_param_base_url = f'/conditions/{pv.latitude},{pv.longitude}'  # CHANGE TO FORECAST FOR FUTURE PREDICTIONS
        requests_param = ''
        for i in range(num_required_calls):
            timedelta_from_args = start + pd.Timedelta(**({'hours': i} if min_resolution else {'days': i}))
            from_param = f'{timedelta_from_args}'
            timedelta_to_args = end if i == num_required_calls - 1 else start + pd.Timedelta(**({'hours': i + 1} if min_resolution else {'days': i + 1}))
            to_param = f'{timedelta_to_args}'

            requests_param += f'{batch_param_base_url}%3Ffrom={from_param}%26to={to_param}'
            if not i == num_required_calls - 1:
                requests_param += ','

        # Global (first 4) & batch params (last) for API call (not in batch requests)
        filter_type = 'min' if min_resolution else 'hr'
        params = {
            "format": "json",
            "filter": f'{resolution}{filter_type}',
            "client_id": XWEATHER_CLIENT_ID,
            "client_secret": XWEATHER_CLIENT_SECRET,
            "requests": requests_param
        }

        # Make API call
        try: 
            response = requests.get(
                f"{XWEATHER_BASE_URL}/batch",
                params=params,
            )
            if response.status_code != 200:
                log.error(
                    f"Failed to get weather data for {pv.name}, Status: {response.status_code}"
                )
                return False
            json_response = response.json()
            if json_response['success'] != True:
                log.error(
                    f"Error in response package for {pv.name}, Recieved error: {response['error']}"
                )
                return False
            
        except Exception as e:
            log.error(f'Failed to get weather data for {pv.name}, Error: {e}')
            return False

        # Create dataframe from API batched responses
        datetime = []
        tamb_series = []
        rh_series = []
        poa_series = []
        for individual_response in json_response['response']['responses']:
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
    def forecast_pv_timestamp_range(self, start: pd.Timestamp, end: pd.Timestamp, pv: PVPanel, resolution: int=30, min_resolution: bool=True, all_models: bool=True) -> pd.DataFrame:
        # Create a dataframe of features
        df_features = self._get_weather_features(start, end, resolution, min_resolution, pv)
        datetime_col = df_features['datetime']
        df_features = self._create_time_features(df_features)

        # Forecast the PV power output
        predictions = self._forecast_pv(df_features, all_models)
        return pd.DataFrame({
            'datetime': datetime_col,
            'Pac_pred': predictions
        })

        
        

        