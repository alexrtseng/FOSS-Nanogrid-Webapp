import datetime
import logging

import requests

from data_collection.smart_meter_reciever import SmartMeterReciever
from data_collection.models import RealTimeMeter, SmartMeter, ThirtyMinAvg

log = logging.getLogger(__name__)
from celery import shared_task
from pymodbus.client import ModbusTcpClient as ModbusClient
from django.db import models
import environ

env = environ.Env()
environ.Env.read_env()
XWEATHER_CLIENT_ID = env("XWEATHER_CLIENT_ID")
XWEATHER_CLIENT_SECRET = env("XWEATHER_CLIENT_SECRET")
REAL_TIME_DATA_BACKLOG = 120  # minutes
XWEATHER_BASE_URL = "https://api.aerisapi.com/conditions"


# get smart meter data task
def _get_sm_data(source_address, host, port, timeout, name, secondary_id=1, regs=5):
    vals = []  # values from smart meter
    log.debug("Connecting to Smart Meter " + name + " ...")
    try:
        client = ModbusClient(host=host, port=port, timeout=timeout)
    except Exception as exc:
        log.error(f"Client connection failed: ({exc})")
        return
    try:
        for addr in source_address:
            response = client.read_holding_registers(
                (addr) - 2, count=3, slave=secondary_id
            )
            if not response.isError():
                rr = SmartMeterReciever.conv_to_32bitfloat(response.registers)
                log.debug(rr)
                vals.append(rr)
            else:
                pass
                log.info(f"Reg. error at {addr}: {response}")
    except Exception as exc:
        log.error(f"Received Modbus Exception({exc}) from Library")
        client.close()
        return

    if len(vals) == regs:
        RealTimeMeter.objects.create(
            smart_meter=SmartMeter.objects.get(field_name=name),
            timestamp=datetime.datetime.now(),
            active=vals[0],
            reactive=vals[1],
            apparent=vals[2],
            power_factor=vals[3],
            freq=vals[4],
        )


# get data from all smart meters; reduces celery task messages
def _get_all_sm_data():
    smart_meters = SmartMeter.objects.all()
    for sm in smart_meters:
        _get_sm_data(
            source_address=SmartMeterReciever.SOURCE_ADDRESS,
            host=sm.ip_address,
            port=SmartMeterReciever.PORT,
            timeout=SmartMeterReciever.TIMEOUT,
            name=sm.field_name,
        )


# celery task for getting all smart meter data
@shared_task
def get_all_sm_data():
    log.info("Getting all smart meter data...")
    _get_all_sm_data()

# calculate weather data in dictionary style as recieved from Xweather API
def _calc_weather_data(weather_data: dict):
    temp_C = 0
    humidity = 0
    feels_like_C = 0
    wind_dir_deg = 0
    wind_speed_kph = 0
    ghi_Wm2 = 0
    precip_mm = 0
    sky = 0
    visibility_km = 0
    dewpoint_C = 0

    for period in weather_data["response"][0]["periods"]:
        temp_C += period["tempC"]
        humidity += period["humidity"]
        feels_like_C += period["feelslikeC"]
        wind_dir_deg += period["windDirDEG"]
        wind_speed_kph += period["windSpeedKPH"]
        ghi_Wm2 += period["solrad"]["ghiWM2"]
        precip_mm += period["precipMM"]
        sky += period["sky"]
        visibility_km += period["visibilityKM"]
        dewpoint_C += period["dewpointC"]

    num_periods = len(weather_data["response"][0]["periods"])
    return {
        "temp_C": temp_C / num_periods,
        "humidity": humidity / num_periods,
        "feels_like_C": feels_like_C / num_periods,
        "wind_dir_deg": wind_dir_deg / num_periods,
        "wind_speed_kph": wind_speed_kph / num_periods,
        "ghi_Wm2": ghi_Wm2 / num_periods,
        "precip_mm": precip_mm / num_periods,
        "sky": sky / num_periods,
        "visibility_km": visibility_km / num_periods,
        "dewpoint_C": dewpoint_C / num_periods,
    }

# get terperature data for one smart meter
def _get_temp_data(sm: SmartMeter, params: dict):
    response = requests.get(
        f"{XWEATHER_BASE_URL}/{sm.latitude},{sm.longitude}",
        params=params,
    )

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


def _calc_thirty_min_avg(dt=datetime.datetime.now()):
    # define parameters for http request to Xweather API
    params = {
        "format": "json",
        "filter": "10min",
        "client_id": "SK97xhuiT4ZtBULDLHvhi",
        "client_secret": "4ZSPcFgnNS4gJOLSDpa6XMxxfMEQ4EpOYirMt46U",
        "from": f"{datetime.datetime.now() - datetime.timedelta(minutes=30)}",
        "to": f"{datetime.datetime.now()}",
    }

    # get all smart meters
    smart_meters = SmartMeter.objects.all()
    log.info("Calculating 30 minute averages...")
    for sm in smart_meters:

        # get all real time meters for the smart meter
        rt_meters = RealTimeMeter.objects.filter(smart_meter=sm)

        # get all real time meters within the last 30 minutes
        lst_30_mins = rt_meters.filter(
            timestamp__gte=dt - datetime.timedelta(minutes=30)
        )
        num_data_points = lst_30_mins.count()

        # calculate the average of the real time meters
        avg = lst_30_mins.aggregate(
            active=models.Avg("active"),
            reactive=models.Avg("reactive"),
            apparent=models.Avg("apparent"),
            power_factor=models.Avg("power_factor"),
            freq=models.Avg("freq"),
        )
        log.debug(f"Thirty minute averages: {avg}")

        # Call for temperature data
        temp_data = _get_temp_data(sm, params)

        # create a new ThirtyMinAvg object
        ThirtyMinAvg.objects.create(
            smart_meter=sm,
            timestamp=dt
            - datetime.timedelta(minutes=15),  # nearest neighbor temporal interpolation
            active=avg["active"],
            reactive=avg["reactive"],
            apparent=avg["apparent"],
            power_factor=avg["power_factor"],
            freq=avg["freq"],
            data_points=num_data_points,
            temp_C=temp_data["temp_C"],
            humidity=temp_data["humidity"],
            feels_like_C=temp_data["feels_like_C"],
            wind_dir_deg=temp_data["wind_dir_deg"],
            wind_speed_kph=temp_data["wind_speed_kph"],
            ghi_Wm2=temp_data["ghi_Wm2"],
            precip_mm=temp_data["precip_mm"],
            sky=temp_data["sky"],
            visibility_km=temp_data["visibility_km"],
            dewpoint_C=temp_data["dewpoint_C"],
        )

        # delete all real time meters older than 30 minutes
        rt_meters.filter(
            timestamp__lt=dt - datetime.timedelta(minutes=REAL_TIME_DATA_BACKLOG)
        ).delete()
    return True


@shared_task
def calc_thirty_min_avg(dt=datetime.datetime.now()):
    _calc_thirty_min_avg(dt)
