from django.urls import path
from . import views

urlpatterns = [
    path("forecast-pv/", views.forecast_pv, name="forcast_pv"),
    path("forecast-ucy-load/", views.forecast_ucy_load, name="forecast_ucy_load"),
    path("forecast-net-load/", views.forecast_net_load, name="forecast_net_load"),
]
