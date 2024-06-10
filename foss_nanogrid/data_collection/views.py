import json
from django.shortcuts import render
from django.http import HttpResponse

from data_collection.add_smart_meters import add_file_sm
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from data_collection.smart_meter_reciever import SmartMeterReciever

# Depricated function for adding smart meters from csv
# def add_sm(request):
#     add_file_sm()
#     return HttpResponse("Hello world!")


# Start data collection (meant for development)
def start_data_collection(request):
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS,
    )

    sm = SmartMeterReciever('Energy Center 1', '172.20.49.4')
    sm.connect()
    args = [sm.source_address, sm.host, sm.port, sm.timeout, sm.name]
    args_json = json.dumps(args)

    PeriodicTask.objects.create(
        interval=schedule,
        name="Get Smart Meter Data",
        task="data_collection.tasks.get_sm_data_task",
        args=(args_json),
    )

    return HttpResponse("Data collection started")
