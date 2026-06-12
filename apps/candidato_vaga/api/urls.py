from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.candidato_vaga.api import test_views
from apps.candidato_vaga.api.views import (
    CandidatoVagaViewSet,
    CandidatoViewSet,
    VagaViewSet,
)

router = DefaultRouter()
router.register('candidatos', CandidatoViewSet, basename='candidato')
router.register('vagas', VagaViewSet, basename='vaga')
router.register('candidato-vagas', CandidatoVagaViewSet, basename='candidato-vaga')

urlpatterns = router.urls

urlpatterns += [
    path('teste/', test_views.candidato_vaga_test_page, name='candidato-vaga-teste-page'),
    path('teste/api/opcoes/', test_views.candidato_vaga_test_options, name='candidato-vaga-teste-options'),
    path('teste/api/candidatos/', test_views.candidato_test_collection, name='candidato-teste-collection'),
    path(
        'teste/api/candidatos/<str:cpf_candidato>/',
        test_views.candidato_test_detail,
        name='candidato-teste-detail',
    ),
    path('teste/api/vagas/', test_views.vaga_test_collection, name='vaga-teste-collection'),
    path('teste/api/vagas/<int:pk>/', test_views.vaga_test_detail, name='vaga-teste-detail'),
    path('teste/api/candidaturas/', test_views.candidatura_test_collection, name='candidatura-teste-collection'),
    path(
        'teste/api/candidaturas/<str:cpf_candidato>/<int:id_vaga>/',
        test_views.candidatura_test_detail,
        name='candidatura-teste-detail',
    ),
]
