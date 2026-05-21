from django.urls import path
from . import views
urlpatterns=[
    path("",views.setor_home),
    path("cargo",views.cargo_home)
]