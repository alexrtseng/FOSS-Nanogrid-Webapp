import json
from django.shortcuts import render
from django.http import HttpResponse

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from data_collection.smart_meter_reciever import SmartMeterReciever
import logging

log = logging.getLogger(__name__)

# Start data collection (meant for development)
def start_data_collection(request):
    try:
        PeriodicTask.objects.get("get_sm_data").delete()
    except:
        pass
    try:
        PeriodicTask.objects.get("calc_thirty_min_avg").delete()
    except:
        pass

    schedule_10_sec, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS,
    )

    schedule_30_min, created = IntervalSchedule.objects.get_or_create(
        every=30,
        period=IntervalSchedule.MINUTES,
    )

    sm = SmartMeterReciever("EC_SM1", "172.20.49.4")
    args = [sm.source_address, sm.host, sm.port, sm.timeout, sm.name]
    args_json = json.dumps(args)

    PeriodicTask.objects.get_or_create(
        interval=schedule_10_sec,
        name="get_sm_data",
        task="data_collection.tasks.get_sm_data",
        args=(args_json),
    )

    PeriodicTask.objects.get_or_create(
        interval=schedule_30_min,
        name="calc_thirty_min_avg",
        task="data_collection.tasks.calc_thirty_min_avg",
    )

    return HttpResponse("Data collection started")
    
