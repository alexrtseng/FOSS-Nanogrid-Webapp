import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

import asyncio

from pymodbus.client import AsyncModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.exceptions import ModbusException as Exception
import datetime, time
from datetime import datetime as dt

SLEEP_INTERVAL = 15 #seconds
TIME_STOP = 2 #minutes of data collection 
end_loop_date = datetime.datetime.now() + datetime.timedelta(minutes=TIME_STOP)

#Register add. for given parameters
tcp_regs = [3060, #Active Power 3-ph
            3068, #Reactive Power 3-ph
            3076, #Apparent Power 3-ph
            3150, #PowerFactor 3-ph
            3110  #Frequency
            ]

class SmartMeterReciever:
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.port = 502
        self.source_address = tcp_regs
        self.timeout = 0.2
        self.client = None

    @staticmethod
    def _conv_to_32bitfloat(logs):
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
    
    def add_register_addr (self, address):
        self.source_address.append(address)

    # Open connection
    async def connect(self):
        log.info("Connecting to Smart Meter " + self.name + " ...")
        try:
            self.client = ModbusClient(host=self.host, port=self.port, timeout=self.timeout)
            await self.client.connect()
        except Exception as exc:
            log.error(f"Client connection failed: ({exc})")
            return False
        return True

    # Get smart meter data for instance; connection must be opened by above function
    async def get_sm_data(self) -> dict | None:
        vals=[]
        try:
            for addr in self.source_address:
                response = await self.client.read_holding_registers((addr)-2,count=3, slave=1)
                if not response.isError():
                    rr = self._conv_to_32bitfloat(response.registers)
                    log.info(rr)
                    vals.append(rr)
                else: 
                    log.error(f"Reg. error at {addr}: {response}")
        except Exception as exc:
            log.error(f"Received Modbus Exception({exc}) from Library")
            await self.client.close()
            return 
        
        log.info('---------------------------------------------')
        return {'active': vals[0], 'reactive': vals[1], 'apparent': vals[2], 'power_factor': vals[3], 'freq': vals[4]}

# Test with two SM; print in log.info
# Connection is not super stable
async def main (lst_SMeters):
    while (datetime.datetime.now() < end_loop_date):
        vals=[]
        for SM in lst_SMeters:
            await SM.connect()
            vals.append(await SM.get_sm_data())
        await asyncio.sleep(SLEEP_INTERVAL)


if __name__ == '__main__':
    lst_sm=[]
    lst_sm.append(SmartMeterReciever('Energy Center 1', '172.20.49.4'))
    lst_sm.append(SmartMeterReciever('STP-1', '172.20.49.3'))

    
    asyncio.run(main(lst_sm))

    print('---------------------------------------------')