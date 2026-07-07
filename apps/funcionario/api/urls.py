from rest_framework.routers import DefaultRouter
from django.urls import path
from apps.funcionario.api import test_views

from apps.funcionario.api.views import (
    ContratoViewSet,
    FolhaPagamentoViewSet,
    FuncionarioAgenteDocumentoViewSet,
    FuncionarioViewSet,
    PlanoCarreiraViewSet,
)

router = DefaultRouter()
router.register('funcionarios', FuncionarioViewSet, basename='funcionario')
router.register('planos-carreira', PlanoCarreiraViewSet, basename='plano-carreira')
router.register('contratos', ContratoViewSet, basename='contrato')
router.register('folhas-pagamento', FolhaPagamentoViewSet, basename='folha-pagamento')
router.register('agente', FuncionarioAgenteDocumentoViewSet, basename='funcionario-agente')

urlpatterns = router.urls

urlpatterns += [
    path('teste/', test_views.funcionario_test_page, name='funcionario-teste-page'),
    path('teste/agente/', test_views.agente_test_page, name='funcionario-agente-teste-page'),
    path('teste/api/agente/upload/', test_views.agente_test_upload, name='funcionario-agente-teste-upload'),
    path('teste/api/agente/perguntar/', test_views.agente_test_perguntar, name='funcionario-agente-teste-perguntar'),
    path('teste/api/opcoes/', test_views.funcionario_test_options, name='funcionario-teste-options'),
    path('teste/api/funcionarios/', test_views.funcionario_test_collection, name='funcionario-teste-collection'),
    path(
        'teste/api/funcionarios/<int:pk>/',
        test_views.funcionario_test_detail,
        name='funcionario-teste-detail',
    ),
]
