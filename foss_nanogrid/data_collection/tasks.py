import datetime
import logging

from data_collection.smart_meter_reciever import SmartMeterReciever
from data_collection.models import RealTimeMeter, SmartMeter, ThirtyMinAvg

log = logging.getLogger(__name__)
from celery import shared_task
from pymodbus.client import ModbusTcpClient as ModbusClient
from django.db import models

REAL_TIME_DATA_BACKLOG = 120  # minutes




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

@shared_task
def get_sm_data(source_address, host, port, timeout, name, secondary_id=1, regs=5):
    _get_sm_data(source_address, host, port, timeout, name, secondary_id, regs)

def _calc_thirty_min_avg(dt=datetime.datetime.now()):
    # get all smart meters
    smart_meters = SmartMeter.objects.all()
    log.info("Calculating 30 minute averages...")
    for sm in smart_meters:

        # get all real time meters for the smart meter
        rt_meters = RealTimeMeter.objects.filter(smart_meter=sm)

        # get all real time meters within the last 30 minutes
        lst_30_mins = rt_meters.filter(timestamp__gte=dt - datetime.timedelta(minutes=30))
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
        )

        # eventually need a function to call api's for temperature, humidity, and irradiance data

        # delete all real time meters older than 30 minutes
        rt_meters.filter(timestamp__lt=dt - datetime.timedelta(minutes=REAL_TIME_DATA_BACKLOG)).delete()
    return True

@shared_task
def calc_thirty_min_avg(dt=datetime.datetime.now()):
    _calc_thirty_min_avg(dt)
