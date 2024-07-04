import pandas as pd
import math
import logging
import environ
import requests

log = logging.getLogger(__name__)

env = environ.Env()
environ.Env.read_env(env_file='././foss_nanogrid/.env')
XWEATHER_CLIENT_ID = env("XWEATHER_CLIENT_ID")
XWEATHER_CLIENT_SECRET = env("XWEATHER_CLIENT_SECRET")
XWEATHER_BASE_URL = "https://api.aerisapi.com/"  # Different from one in data_collection (for batch feature)

# Make batch (requests) param for API call (signifigantly reduces number of calls to API)
def get_weather_data_batch(start: pd.Timestamp, end: pd.Timestamp, longitude, latitude, resolution, min_resolution: bool) -> pd.DataFrame | bool:    
    num_required_calls = math.ceil(((end - start).seconds / 3600) + (end - start).days * 24) if min_resolution else (end - start).days + 1
    assert num_required_calls <= 31, "Number of requests must be under 31"
    assert num_required_calls > 0, "Number of requests must be greater than 0"
    log.debug(f'Num of calls in batch: {num_required_calls}')
    batch_param_base_url = f'/conditions/{longitude},{latitude}'  # CHANGE TO FORECAST FOR FUTURE PREDICTIONS
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
                f"Failed to get weather data for Long: {longitude}, Lat: {latitude}, Status: {response.status_code}"
            )
            return False
        response_data = response.json()
        if response_data['success'] != True:
            log.error(
                f"Error in response package for Long: {longitude}, Lat: {latitude}, Recieved error: {response['error']}"
            )
            return False
        
    except Exception as e:
        log.error(f'Failed to get weather data for Long: {longitude}, Lat: {latitude}, Error: {e}')
        return False
    
    return response_data