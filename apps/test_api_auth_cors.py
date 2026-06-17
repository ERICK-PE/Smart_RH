from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework_simplejwt.views import TokenRefreshView

from Smart_RH.api_auth import SmartRHTokenObtainPairSerializer, SmartRHTokenObtainPairView


@override_settings(ALLOWED_HOSTS=['testserver'])
class APIAuthCorsConfigurationTests(SimpleTestCase):
    def test_cors_headers_configurado_com_origens_restritas(self):
        self.assertIn('corsheaders', settings.INSTALLED_APPS)
        self.assertIn('corsheaders.middleware.CorsMiddleware', settings.MIDDLEWARE)
        self.assertLess(
            settings.MIDDLEWARE.index('corsheaders.middleware.CorsMiddleware'),
            settings.MIDDLEWARE.index('django.middleware.common.CommonMiddleware'),
        )
        self.assertFalse(getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False))
        self.assertIn('http://localhost:5173', settings.CORS_ALLOWED_ORIGINS)
        self.assertEqual(settings.CORS_URLS_REGEX, r'^/api/.*$')

    def test_cors_responde_para_origem_local_permitida(self):
        response = self.client.options(
            '/api/',
            HTTP_ORIGIN='http://localhost:5173',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:5173')

    def test_jwt_e_session_authentication_configurados(self):
        authentication_classes = settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']

        self.assertEqual(
            authentication_classes,
            [
                'rest_framework_simplejwt.authentication.JWTAuthentication',
                'rest_framework.authentication.SessionAuthentication',
            ],
        )
        self.assertEqual(settings.SIMPLE_JWT['AUTH_HEADER_TYPES'], ('Bearer',))

    def test_rotas_jwt_resolvem_sob_api_auth(self):
        self.assertIs(resolve('/api/auth/token/').func.view_class, SmartRHTokenObtainPairView)
        self.assertIs(resolve('/api/auth/token/refresh/').func.view_class, TokenRefreshView)

    def test_token_serializer_resolve_username_publico_do_candidato(self):
        serializer = SmartRHTokenObtainPairSerializer()
        user = SimpleNamespace(get_username=lambda: 'candidato:joao')
        candidato = SimpleNamespace(user_id=10, user=user)

        with patch('Smart_RH.api_auth.Candidato.objects') as candidato_manager:
            candidato_manager.select_related.return_value.filter.return_value.first.return_value = candidato

            self.assertEqual(
                serializer.get_profile_auth_username('candidato', 'joao'),
                'candidato:joao',
            )

    def test_token_endpoint_rejeita_input_incompleto_sem_expor_detalhe_sensivel(self):
        response = self.client.post('/api/auth/token/', {}, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json())
        self.assertIn('password', response.json())
        self.assertNotIn('traceback', response.content.decode().lower())
