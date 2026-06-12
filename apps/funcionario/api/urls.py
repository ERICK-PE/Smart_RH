from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.urls import path

from apps.funcionario.api.views import (
    ContratoViewSet,
    FuncionarioViewSet,
    PlanoCarreiraViewSet,
)

router = DefaultRouter()
router.register('funcionarios', FuncionarioViewSet, basename='funcionario')
router.register('planos-carreira', PlanoCarreiraViewSet, basename='plano-carreira')
router.register('contratos', ContratoViewSet, basename='contrato')

urlpatterns = router.urls

if settings.DEBUG:
    from apps.funcionario.api import test_views

    urlpatterns += [
        path('teste/', test_views.funcionario_test_page, name='funcionario-teste-page'),
        path('teste/api/opcoes/', test_views.funcionario_test_options, name='funcionario-teste-options'),
        path('teste/api/funcionarios/', test_views.funcionario_test_collection, name='funcionario-teste-collection'),
        path(
            'teste/api/funcionarios/<int:pk>/',
            test_views.funcionario_test_detail,
            name='funcionario-teste-detail',
        ),
    ]
