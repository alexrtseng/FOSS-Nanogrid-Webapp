import pandas as pd
import logging
import math
log = logging.getLogger(__name__)

def num_req_calls_valid(start, end, min_resolution) -> bool:
    num_required_calls = (
        math.ceil(((end - start).seconds / 3600) + (end - start).days * 24)
        if min_resolution
        else (end - start).days + 1
    )
    if num_required_calls <= 0:
        log.info("Invalid info/ request. Start and end are too close")
        return False
    elif num_required_calls > 31:
        log.info(
            "Invalid info/ request. Range too large of resolution; cannot batch API calls"
        )
        return False
    else:
        return True


def start_end_time_valid(_start, _end) -> bool:
    try:
        start = pd.Timestamp(_start)
        end = pd.Timestamp(_end)
        assert start < end, "Start must be before end"
        assert end < pd.Timestamp.now() + pd.Timedelta(
            days=15
        ), "End must be within 15 days of now"
    except Exception as e:
        log.info(f"Invalid start or end timestamps: {e}")
        return False

    return start, end

# For forecasting views, deal with generic params (meant to clean up code)
def get_forecast_params(request):
    start = request.query_params["start"]
    end = request.query_params["end"]
    if "resolution" in request.query_params:
        resolution = request.query_params["resolution"]
    else:
        resolution = 30
    if "min_resolution" in request.query_params:
        min_resolution = request.query_params["min_resolution"].lower() in [
            "true",
            "1",
            "t",
            "y",
            "yes",
        ]
    else:
        min_resolution = True

    return start, end, resolution, min_resolution   