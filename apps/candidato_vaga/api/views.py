from django.shortcuts import render
from django.http import HttpResponse

def candidato_home(request):
    return HttpResponse("Teste candidato")
def vaga_home(request):
    return HttpResponse("Teste Vaga")
def candidato_vaga_home(request):
    return HttpResponse("Teste Candidato Vaga")