from django.urls import path
from . import views

urlpatterns = [
    path("forecast-pv/", views.forecast_pv, name="forcast_pv"),
]
