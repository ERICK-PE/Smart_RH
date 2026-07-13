from rest_framework.routers import DefaultRouter

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
