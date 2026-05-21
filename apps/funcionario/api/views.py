from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def funcionario_home(request):
    return HttpResponse("Teste funcionario")

def carreira_home(request):
    return HttpResponse("Teste Plano de carreira")

def contrato_home(request):
    return HttpResponse("Teste Contrato")