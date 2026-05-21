from django.shortcuts import render
from django.http import HttpResponse

def avaliacao_desempenho_home(request):
    return HttpResponse("Teste Avaliação Desempenho")

def analise_comportamental_home(request):
    return HttpResponse("Teste Analise")