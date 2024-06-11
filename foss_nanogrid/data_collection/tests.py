from importlib.metadata import distribution
from numbers import Real
from django.test import TestCase
import datetime

from .models import RealTimeMeter, SmartMeter, ThirtyMinAvg
from .tasks import _calc_thirty_min_avg

# Create your tests here.
class DataCollectionTestCase(TestCase):
    def setUp(self):
        SmartMeter.objects.create(
            ip_address="172.20.49.4",
            field_name="EC_SM1",
            distribution_board="Energy Centre",
            latitude=35.146506,
            longitude=33.415653,
            feeder_connection="TRS4",
            feeder="Incomer",
            serial_no="ME-1801C724-02",
            modbus_port=502,
            mac_address="6078089165",
            comments="This is a test",
            username="admin",
            password="0",
            secondary_id=1,
        )

        for i in range(10):
            RealTimeMeter.objects.create(
                smart_meter=SmartMeter.objects.get(field_name="EC_SM1"),
                timestamp=datetime.datetime.now(),
                active=i,
                reactive=i,
                apparent=i,
                power_factor=i,
                freq=i,
            )

        RealTimeMeter.objects.create(
            smart_meter=SmartMeter.objects.get(field_name="EC_SM1"),
            timestamp=datetime.datetime.now() - datetime.timedelta(minutes=130),
            active=10,
            reactive=10,
            apparent=10,
            power_factor=10,
            freq=10,
        )

    def test_calc_thirty_min_avg(self):
        _calc_thirty_min_avg()
        self.assertEqual(RealTimeMeter.objects.all().count(), 10)  # test deletion of old data
        self.assertEqual(ThirtyMinAvg.objects.all().count(), 1)  # test creation of 30 min avg
        self.assertEqual(
            ThirtyMinAvg.objects.get().active, 4.5
        )
