from importlib.util import find_spec

from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from Smart_RH.api_auth import SmartRHTokenObtainPairView


def api_root_view(request):
    """Retorna catalogo de descoberta da API publica sob /api/."""
    drf_spectacular_available = bool(find_spec('drf_spectacular'))
    docs = {
        'schema': request.build_absolute_uri('schema/') if drf_spectacular_available else None,
        'swagger': request.build_absolute_uri('docs/') if drf_spectacular_available else None,
        'redoc': request.build_absolute_uri('redoc/') if drf_spectacular_available else None,
    }

    return JsonResponse({
        'name': 'Smart-RH API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'token': request.build_absolute_uri('auth/token/'),
                'refresh': request.build_absolute_uri('auth/token/refresh/'),
            },
            'setor': request.build_absolute_uri('setor/'),
            'funcionario': request.build_absolute_uri('funcionario/'),
            'avaliacao': request.build_absolute_uri('avaliacao/'),
            'candidato': request.build_absolute_uri('candidato/'),
        },
        'documentation': docs,
        'documentation_enabled': drf_spectacular_available,
    })


urlpatterns = [
    path('auth/token/', SmartRHTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('setor/', include('apps.setor.api.urls')),
    path('funcionario/', include('apps.funcionario.api.urls')),
    path('avaliacao/', include('apps.avaliacao.api.urls')),
    path('candidato/', include('apps.candidato_vaga.api.urls')),
]

if find_spec('drf_spectacular'):
    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

    urlpatterns += [
        path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
        path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
        path('redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),
    ]

urlpatterns.append(path('', api_root_view, name='smart-rh-api-root'))
