from rest_framework.routers import DefaultRouter

from apps.avaliacao.api.views import (
    AnaliseComportamentalViewSet,
    AvaliacaoDesempenhoViewSet,
)

router = DefaultRouter()
router.register(
    'analises-comportamentais',
    AnaliseComportamentalViewSet,
    basename='analise-comportamental',
)
router.register(
    'avaliacoes-desempenho',
    AvaliacaoDesempenhoViewSet,
    basename='avaliacao-desempenho',
)

urlpatterns = router.urls
