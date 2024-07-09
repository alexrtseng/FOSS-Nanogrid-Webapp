import numpy as np
import pandas as pd
import xgboost as xgb
import logging
from ..helper_functions.weather_api import get_weather_data_batch
from data_collection.models import SmartMeter

log = logging.getLogger(__name__)


# Number of features for the model
NUM_OF_FEATURES = 8

# Number of models
NUM_OF_MODELS = 5

"""
Models have been trained seperately using XGBoost with featurs: 
['minute', 'day_of_week', 'day_of_year', 'month', 'Tamb-temp', 'humidity', 'precipMM', 'GHI-GhPyr']
and params: {
max_depth=3, n_estimators=300, early_stopping_rounds=50, objective='reg:squarederror', n_jobs=-1
}
This was the best model out of LSTM, and the given model. Models trained/tested on 8 months of GPI logger_1_min data 
and cross validated with 25 folds for a avg cross-validation RMSE of 0.16 MW and MAPE (whole set) 8.8 percent.
Model files have been saved in native XGBoost binary format in the load_models_v2 folder. Version 1 of the models is
trained without artificial data and struggles in summer months. Version 2+ tries to resolve this issue by adding artifical 
summer data. Version 4 is the most recent and solves small train set issues by reducing # of folds. 
Naming convention should follow: 'xgboost_load_model_{#}.bin' with # indexing from 0

ALL UNITS CONSIDERED IN MW
*Pay attention to timezones if modifying*; internally uses UTC for model, but public functions should use Asia/
Nicosia for parameters and output in the same timezone
"""

class LoadPredict():
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
            reg.load_model(f"forecasting/load_forecasting/load_models_versions/load_models_v4/xgboost_load_model_{i}.bin")
            regs.append(reg)
        return regs
    
    # Return dataframe with weather features and datetime column given a time range and resolution
    def _get_weather_features(self, start: pd.Timestamp, end: pd.Timestamp, resolution, min_resolution: bool, sm: SmartMeter) -> pd.DataFrame:
        # Get weather data from API
        response_data = get_weather_data_batch(start=start, end=end, longitude=sm.longitude, latitude=sm.latitude, resolution=resolution, min_resolution=min_resolution)

        # Create dataframe from API batched responses
        datetime = []
        tamb_series = []
        rh_series = []
        precip_series = []
        ghi_series = [] # in WM2
        for individual_response in response_data['response']['responses']:
            if individual_response['success'] == True:
                for period in individual_response['response'][0]['periods']:
                    tamb_series.append(period['tempC'])
                    rh_series.append(period['humidity'])
                    precip_series.append(period['precipMM'])
                    ghi_series.append(period['solrad']['ghiWM2'])
                    datetime.append(period['dateTimeISO'])    # ALTERNATIVE IS ValidTime?
            else:
                log.error(
                    f"Error in individual response for {sm.field_name}, Recieved error: {individual_response['error']}"
                )

        df = pd.DataFrame({
            'datetime': datetime,
            'Tamb-temp': tamb_series,
            'humidity': rh_series,
            'precipMM': precip_series,
            'GHI-GhPyr': ghi_series
        })
        df['datetime'] = (pd
                          .to_datetime(df['datetime'], utc=True)
                        )

        return df

    # Create time features from a dataframe with a datetime column
    def _create_time_features(self, _df) -> pd.DataFrame:
        df = _df.copy()
        assert 'datetime' in df.columns, "Input dataframe must have a 'datetime' column"

        df['minute'] = df['datetime'].dt.minute + df['datetime'].dt.hour * 60
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['day_of_year'] = df['datetime'].dt.dayofyear
        df['month'] = df['datetime'].dt.month

        return df[['minute', 'day_of_week', 'day_of_year', 'month', 'Tamb-temp', 'humidity', 'precipMM', 'GHI-GhPyr']]
    

    # Helper function to forecast load power using pre-trained regression models
    # Input: model input features and a boolean all_models to use all models or just the best
    def _forecast_load(self, input_features: pd.DataFrame) -> np.array:
        # Check input features
        assert (
            input_features.shape[1] == NUM_OF_FEATURES
        ), f"Input features must have {NUM_OF_FEATURES} columns"

        sum = np.zeros(input_features.shape[0])
        for reg in self.regs:
            sum += reg.predict(input_features)
        
        return sum / len(self.regs)

    # Forecast load Power for range between start and end with minute resolution of resolution
    def forecast_load_timestamp_range(self, start: pd.Timestamp, end: pd.Timestamp, sm: SmartMeter, resolution: int=30, min_resolution: bool=True) -> pd.DataFrame:
        # Check legitimate input
        assert start < end, "Start must be before end"
        # Times will get converted to UTC after API call
        # Create a dataframe of features
        df_features = self._get_weather_features(start, end, resolution, min_resolution, sm)
        if not isinstance(df_features, pd.DataFrame):
            return False
        
        datetime_col = df_features['datetime']
        datetime_col = datetime_col.dt.tz_convert('Asia/Nicosia')
        df_features = self._create_time_features(df_features)

        # Forecast the load power 
        predictions = self._forecast_load(df_features)
        return pd.DataFrame({
            'datetime': datetime_col,
            'Pac_pred': predictions
        })
    
    # Take predictions data from (columns: datetime, Pac_pred) and creates json file in SolarCast format
    # **kwargs: sm - SmartMeter object, date_run - date the forecast model was run
    @staticmethod
    def forecasted_power_to_dict(_predictions: pd.DataFrame, model='XGBoost_load_v2', **kwargs) -> dict:
        predictions = _predictions.sort_values(by='datetime').copy()
        values = []
        if 'sm' in kwargs:
            sm = SmartMeter.objects.get(field_name=kwargs['sm'])
        else: 
            sm = SmartMeter.objects.get(field_name='EC_SM2')

        for index, row in predictions.iterrows():
            values.append({
                'Timestamp': row['datetime'],
                'kW': row['Pac_pred']
            })

        if 'sm' in kwargs and len(values) >= 1:
            forecast_dict = {
                'Grid': 'UCY Microgrid',
                'Reference SM': sm.field_name,     # This unimportant... can be used for referencing specific sm attributes internal prediction parameters
                'latitude': sm.latitude,
                'longitude': sm.longitude,
                'unit': 'MW',
                'Timezone': 'Asia/Nicosia',
                'model': model,
                'date_run' : pd.Timestamp.now(tz='UTC') if 'date_run' not in kwargs else kwargs['date_run'],
                'forecasted_dates' : f"{values[0]['Timestamp']} to {values[-1]['Timestamp']}",
                'values': values
            }
        else:
            forecast_dict = {
                'values': values
            }

        return forecast_dict
        
        

        