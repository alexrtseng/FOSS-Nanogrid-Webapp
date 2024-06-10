import logging

from data_collection.smart_meter_reciever import SmartMeterReciever
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
from celery import shared_task
from pymodbus.client import ModbusTcpClient as ModbusClient
from celery import app
import time

@shared_task
def get_sm_data_task(source_address, host, port, timeout, name):
    vals=[]
    log.info("Connecting to Smart Meter " + name + " ...")
    try:
        client = ModbusClient(host=host, port=port, timeout=timeout)
    except Exception as exc:
        log.error(f"Client connection failed: ({exc})")
        return False
    try:
        for addr in source_address:
            response = client.read_holding_registers((addr)-2,count=3, slave=1)
            if not response.isError():
                rr = SmartMeterReciever._conv_to_32bitfloat(response.registers)
                log.info(rr)
                vals.append(rr)
            else: 
                pass
                log.error(f"Reg. error at {addr}: {response}")
    except Exception as exc:
        log.error(f"Received Modbus Exception({exc}) from Library")
        client.close()
        return 
    
    log.info('---------------------------------------------')
    if len(vals) >= 1:
        return {'active': vals[0], 'reactive': vals[1], 'apparent': vals[2], 'power_factor': vals[3], 'freq': vals[4]}
    else:
        return False
