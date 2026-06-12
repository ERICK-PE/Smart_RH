from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.avaliacao.api import test_views
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

urlpatterns += [
    path('teste/', test_views.avaliacao_test_page, name='avaliacao-teste-page'),
    path('teste/api/opcoes/', test_views.avaliacao_test_options, name='avaliacao-teste-options'),
    path('teste/api/funcionarios/', test_views.funcionario_test_collection, name='avaliacao-funcionario-teste-collection'),
    path('teste/api/analises/', test_views.analise_test_collection, name='analise-teste-collection'),
    path('teste/api/analises/<int:pk>/', test_views.analise_test_detail, name='analise-teste-detail'),
    path('teste/api/avaliacoes/', test_views.avaliacao_test_collection, name='avaliacao-teste-collection'),
    path('teste/api/avaliacoes/<int:pk>/', test_views.avaliacao_test_detail, name='avaliacao-teste-detail'),
]
