import logging as log
from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.exceptions import ModbusException as Exception
import datetime, time
from datetime import datetime as dt

sleep_interval = 15 #seconds
time_stop = 2 #minutes of data collection 
end_loop_date = datetime.datetime.now() + datetime.timedelta(minutes=time_stop)

tcp_regs = [3060, #Active Power 3-ph
            3068, #Reactive Power 3-ph
            3076, #Apparent Power 3-ph
            3150, #PowerFactor 3-ph
            3110  #Frequency
            ]

class SmartMeter:
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.port = 502
        self.source_address = tcp_regs
        self.timeout = 0.2
    
    def add_register_addr (self, address):
        self.source_address.append(address)


def conv_to_32bitfloat(logs):
    i = 0
    rr = []
    rr.append(dt.fromtimestamp(
        time.time()).strftime("%d-%m-%Y, %H:%M:%S"))
    while i < len(logs)-1:
        decoder = BinaryPayloadDecoder.fromRegisters(
            [logs[i], logs[i+1]], Endian.BIG, wordorder=Endian.LITTLE)
        decoder = decoder.decode_32bit_float()
        rr.append(decoder)
        i += 2
    return tuple(i for i in rr)

def main (lst_SMeters):
    while (datetime.datetime.now() < end_loop_date):
        vals=[]
        try:
            for SM in lst_SMeters:
                print("Connecting to Smart Meter " + SM.name + " ...")
                try:
                    client = ModbusClient(host=SM.host, port= SM.port, timeout=SM.timeout)
                    for addr in SM.source_address:
                        rr = client.read_holding_registers((addr)-2,count=3, slave=1).registers
                        rr=conv_to_32bitfloat(rr)
                        print(rr)
                        vals.append(rr)
                except Exception as exc:
                    print(f"Received Modbus Exception({exc}) from Library")
                    client.close()
                    continue
                print('---------------------------------------------')
        except:
            client.close()
            time.sleep(5)
            continue
        
        time.sleep(sleep_interval)


if __name__ == '__main__':
    lst_sm=[]
    lst_sm.append(SmartMeter('Energy Center 1', '172.20.49.4'))
    lst_sm.append(SmartMeter('STP-1', '172.20.49.3'))

    
    main(lst_sm)

    print('---------------------------------------------')