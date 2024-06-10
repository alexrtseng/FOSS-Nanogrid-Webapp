from django.urls import path
from . import views

urlpatterns = [
    # path('data_collection/', views.add_sm, name='add_sm'), #add smart meters from csv 
    path('start_data_collection/', views.start_data_collection, name='start_data_collection'),
]