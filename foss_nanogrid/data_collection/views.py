import json
from django.shortcuts import render
from django.http import HttpResponse

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from data_collection.smart_meter_reciever import SmartMeterReciever


# Start data collection (meant for development)
def start_data_collection(request):
    try:
        PeriodicTask.objects.get("get_sm_data").delete()
    except:
        pass

    schedule, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS,
    )

    sm = SmartMeterReciever("EC_SM1", "172.20.49.4")
    args = [sm.source_address, sm.host, sm.port, sm.timeout, sm.name]
    args_json = json.dumps(args)

    PeriodicTask.objects.get_or_create(
        interval=schedule,
        name="get_sm_data",
        task="data_collection.tasks.get_sm_data_task",
        args=(args_json),
    )

    return HttpResponse("Data collection started")
    
