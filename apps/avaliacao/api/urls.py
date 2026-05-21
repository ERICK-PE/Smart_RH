from django.urls import path
from . import views
urlpatterns=[
    path('',views.avaliacao_desempenho_home),
    path('analise/',views.analise_comportamental_home)
]