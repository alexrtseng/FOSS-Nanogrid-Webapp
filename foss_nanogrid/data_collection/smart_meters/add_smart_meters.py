# Script to read cvx data on smart meters and store in database

from dataclasses import field
from ipaddress import ip_address
import logging

from data_collection.models import SmartMeter
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
FILE_NAME = 'data_collection/smart_meters/ucy_sm_modbus_map.csv'

def add_file_sm(file_name):
    import csv
    with open(FILE_NAME, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            print(row)
            SmartMeter.objects.create(
                distribution_board=row[0],
                field_name=row[1],
                latitude=row[2],
                longitude=row[3],
                feeder_connection=row[4],
                feeder=row[5],
                serial_no=row[6],
                ip_address=row[7],
                modbus_port=row[8],
                mac_address=row[9],
                comments=row[11],
                username=row[12],
                password=row[13],
                secondary_id=row[14]
            )