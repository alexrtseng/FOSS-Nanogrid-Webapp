import datetime
import logging

from data_collection.smart_meter_reciever import SmartMeterReciever
from data_collection.models import RealTimeMeter, SmartMeter

log = logging.getLogger(__name__)
from celery import shared_task
from pymodbus.client import ModbusTcpClient as ModbusClient
from celery import app


# get smart meter data task; meant to be run by beat
@shared_task
def get_sm_data_task(source_address, host, port, timeout, name, secondary_id=1, regs=5):
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
