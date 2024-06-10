from django.shortcuts import render
from django.http import HttpResponse

from data_collection.add_smart_meters import add_file_sm

def add_sm(request):
    add_file_sm()
    return HttpResponse("Hello world!")