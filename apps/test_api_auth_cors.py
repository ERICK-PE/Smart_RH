import json
from types import SimpleNamespace

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from Smart_RH.api_urls import auth_me_view


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
        self.assertIs(resolve('/api/auth/token/').func.view_class, TokenObtainPairView)
        self.assertIs(resolve('/api/auth/token/refresh/').func.view_class, TokenRefreshView)

    def test_token_endpoint_rejeita_input_incompleto_sem_expor_detalhe_sensivel(self):
        response = self.client.post('/api/auth/token/', {}, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json())
        self.assertIn('password', response.json())
        self.assertNotIn('traceback', response.content.decode().lower())


class FakeGroups:
    def values_list(self, *args, **kwargs):
        return ['rh']


class FakeUser:
    pk = 1
    is_authenticated = True
    is_staff = True
    is_superuser = False
    groups = FakeGroups()

    def get_username(self):
        return 'admin_rh'

    def get_full_name(self):
        return 'Admin RH'

    def get_all_permissions(self):
        return {'funcionario.view_rh_panel'}

    def has_perm(self, permission):
        return permission == 'funcionario.view_rh_panel'


class AuthMeEndpointTests(SimpleTestCase):
    def test_auth_me_exige_autenticacao(self):
        request = APIRequestFactory().get('/api/auth/me/')
        response = auth_me_view(request)

        self.assertIn(response.status_code, [401, 403])

    def test_auth_me_retorna_sessao_admin_sem_dados_sensiveis(self):
        user = FakeUser()
        request = APIRequestFactory().get('/api/auth/me/')
        force_authenticate(request, user=user)

        response = auth_me_view(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], user.pk)
        self.assertEqual(data['username'], 'admin_rh')
        self.assertEqual(data['nome'], 'Admin RH')
        self.assertEqual(data['profile'], 'rh_admin')
        self.assertTrue(data['is_staff'])
        self.assertNotIn('password', data)
