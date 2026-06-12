from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.setor.api import test_views
from apps.setor.api.views import CargoViewSet, SetorViewSet

router = DefaultRouter()
router.register('setores', SetorViewSet, basename='setor')
router.register('cargos', CargoViewSet, basename='cargo')

urlpatterns = router.urls

urlpatterns += [
    path('teste/', test_views.setor_test_page, name='setor-teste-page'),
    path('teste/api/setores/', test_views.setor_test_collection, name='setor-teste-collection'),
    path('teste/api/setores/<int:pk>/', test_views.setor_test_detail, name='setor-teste-detail'),
    path('teste/api/cargos/', test_views.cargo_test_collection, name='cargo-teste-collection'),
    path('teste/api/cargos/<int:pk>/', test_views.cargo_test_detail, name='cargo-teste-detail'),
]
