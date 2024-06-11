from django.urls import path
from . import views

urlpatterns = [
    path("start/", views.start_data_collection, name="start_data_collection"),
]
