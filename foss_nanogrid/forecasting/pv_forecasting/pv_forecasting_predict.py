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
MODEL_ACC_WEIGHTS = [
    160.71058409,
    178.80454954,
    121.02804917,
    120.35546842,
    131.01931725,
    135.04967787,
]

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

    # Calculate the POA from the GHI; CURRENTLY JUST CHATGPT FILLER
    def calculate_poa_irradiance(DNI, GHI, DHI, theta_z, phi_s, beta, phi, albedo=0.2):
        # Convert angles to radians
        theta_z_rad = math.radians(theta_z)
        phi_s_rad = math.radians(phi_s)
        beta_rad = math.radians(beta)
        phi_rad = math.radians(phi)
        
        # Calculate angle of incidence
        cos_theta_i = (math.cos(theta_z_rad) * math.cos(beta_rad) + 
                    math.sin(theta_z_rad) * math.sin(beta_rad) * math.cos(phi_s_rad - phi_rad))
        
        # Beam component on POA
        I_beam = DNI * max(cos_theta_i, 0)
        
        # Diffuse component on POA (isotropic model)
        I_diffuse = DHI * (1 + math.cos(beta_rad)) / 2
        
        # Ground-reflected component on POA
        I_ground = GHI * albedo * (1 - math.cos(beta_rad)) / 2
        
        # Total POA irradiance
        I_POA = I_beam + I_diffuse + I_ground
        
        return I_POA
    
    # Return dataframe with weather features and datetime column given a time range and resolution
    def _get_weather_features(self, start: pd.Timestamp, end: pd.Timestamp, resolution, min_resolution: bool, pv: PVPanel) -> pd.DataFrame:
        # Make batch (requests) param for API call (signifigantly reduces number of calls to API)
        num_required_calls = math.ceil((end - start).seconds / 3600) if min_resolution else (end - start).days + 1
        assert num_required_calls <= 31, "Number of requests must be under 31"
        batch_param_base_url = f'/conditions/{pv.latitude},{pv.longitude}'
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

        response = requests.get(
            f"{XWEATHER_BASE_URL}/batch",
            params=params,
        )

        return response.json()

        # time_range = pd.date_range(start=start, end=end, freq=f'{resolution}{'min' if min_resolution else 'h'}')

        if response.status_code == 200:
            try:
                response_dict = response.json()
                return _calc_weather_data(response_dict)

            except Exception as e:
                log.error(
                    f"Failed to get temperature data for SM {sm.field_name}, Error: {e}"
                )
                return False
        else:
            log.info(
                f"API temperature call failed for SM {sm.field_name}, Status: {response.status_code}"
            )
            return False

        # Get weather data from start to end
        weather_data = pd.DataFrame()
        weather_data['Tamb'] = np.random.randint(15, 35, size=(end-start).seconds // 60)
        weather_data['RH'] = np.random.randint(30, 80, size=(end-start).seconds // 60)
        weather_data['POA'] = np.random.randint(300, 1000, size=(end-start).seconds // 60)

        return weather_data

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
    def _forecast_pv(self, input_features: pd.DataFrame, all_models=True) -> np.array:
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
            
            return sum / sum(MODEL_ACC_WEIGHTS)

    # Forecast PV Power Output for range between start and end with minute resolution of resolution
    def forecast_pv_timestamp_range(self, start: pd.Timestamp, end: pd.Timestamp, resolution: int=30) -> np.array:
        # Create a dataframe of features
        time_range = pd.date_range(start=start, end=end, freq=f'{resolution}T')

        