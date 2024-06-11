from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("rt-meters/", views.rt_meters, name="rt_meters"),
]
