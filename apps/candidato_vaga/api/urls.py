from rest_framework.routers import DefaultRouter

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
