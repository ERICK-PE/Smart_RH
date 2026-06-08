from rest_framework.routers import DefaultRouter

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
