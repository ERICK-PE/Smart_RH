from django.urls import path
from . import views
urlpatterns=[
    path('',views.candidato_home),
    path('vaga',views.vaga_home),
    path('cv',views.candidato_vaga_home)
]