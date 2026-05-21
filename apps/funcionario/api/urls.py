from django.urls import path
from . import views
urlpatterns=[
    path('',views.funcionario_home),
    path('carreira/',views.carreira_home),
    path('contrato/',views.contrato_home)
]