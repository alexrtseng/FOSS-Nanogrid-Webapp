import json
from django.shortcuts import render
from django.http import HttpResponse

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from data_collection.smart_meter_reciever import SmartMeterReciever
import logging

from .models import SmartMeter

log = logging.getLogger(__name__)


# Start data collection (meant for development)
def start_data_collection(request):
    schedule_10_sec, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS,
    )

    schedule_30_min, created = IntervalSchedule.objects.get_or_create(
        every=30,
        period=IntervalSchedule.MINUTES,
    )

    # Start real-time data collection – failed connections will not be retried (must implement in future)
    try:
        PeriodicTask.objects.get(name="get_all_sm_data").delete()
    except Exception as e:
        log.error(f"Failed to delete get_all_sm_data: {e}")
        pass

    try:
        PeriodicTask.objects.get_or_create(
            interval=schedule_10_sec,
            name="get_all_sm_data",
            task="data_collection.tasks.get_all_sm_data",
            args=[],
        )
    except Exception as e:
        log.error(f"Failed to start data collection: {e}")

    # Start 30 min avg calculations
    try:
        PeriodicTask.objects.get(name="calc_thirty_min_avg").delete()
    except:
        pass

    PeriodicTask.objects.get_or_create(
        interval=schedule_30_min,
        name="calc_thirty_min_avg",
        task="data_collection.tasks.calc_thirty_min_avg",
    )

    return HttpResponse("Data collection started")
