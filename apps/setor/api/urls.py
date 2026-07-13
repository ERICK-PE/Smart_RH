from rest_framework.routers import DefaultRouter

from apps.setor.api.views import CargoViewSet, SetorViewSet

router = DefaultRouter()
router.register('setores', SetorViewSet, basename='setor')
router.register('cargos', CargoViewSet, basename='cargo')

urlpatterns = router.urls
