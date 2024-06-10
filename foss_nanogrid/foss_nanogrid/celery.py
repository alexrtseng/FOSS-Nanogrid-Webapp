# Celery setup
import os
from celery import Celery
from django.conf import settings  


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foss_nanogrid.settings')
  
app = Celery('foss_nanogrid')
 
#setting settings.py as default configuration for CELERY
app.config_from_object('django.conf:settings',namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

#this TASK_QUEUE_NAME will contain name of SQS queue and we'll define it later in settings.py
app.conf.task_default_queue = settings.TASK_QUEUE_NAME 
app.conf.task_default_exchange = settings.TASK_QUEUE_NAME
app.conf.task_default_routing_key = settings.TASK_QUEUE_NAME