from django.urls import path
from . import views

urlpatterns = [
    path("devices", views.devices, name="devices"),
    path("rt-all-meters/", views.rt_all_meters, name="rt_all_meters"),
]
