import numpy as np
import pandas as pd
import xgboost as xgb

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
    # Load the models from files
    def _load_models(self) -> list:
        regs = []
        for i in range(NUM_OF_MODELS):
            reg = xgb.XGBRegressor()
            reg.load_model(f"pv_models_v1/xgboost_pv_model_{i}.bin")
            regs.append(reg)
        return regs

    # Contructor
    def __init__(self):
        self.regs = self._load_models()


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

    # Forecast PV Power Output for tomorrow
