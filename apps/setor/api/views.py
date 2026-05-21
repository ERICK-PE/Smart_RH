from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def setor_home(request):
    return HttpResponse("Teste setor")

def cargo_home(request):
    return HttpResponse("Teste cargo")