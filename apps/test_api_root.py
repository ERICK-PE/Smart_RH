from importlib.util import find_spec

from django.test import SimpleTestCase, override_settings
from django.urls import Resolver404, resolve


@override_settings(ALLOWED_HOSTS=['testserver'])
class APIRootRoutingTests(SimpleTestCase):
    def test_api_root_retorna_catalogo_de_endpoints(self):
        response = self.client.get('/api/')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['name'], 'Smart-RH API')
        self.assertIn('/api/auth/token/', data['endpoints']['auth']['token'])
        self.assertIn('/api/auth/token/refresh/', data['endpoints']['auth']['refresh'])
        self.assertIn('/api/setor/', data['endpoints']['setor'])
        self.assertIn('/api/funcionario/', data['endpoints']['funcionario'])
        self.assertIn('/api/avaliacao/', data['endpoints']['avaliacao'])
        self.assertIn('/api/candidato/', data['endpoints']['candidato'])

    def test_api_includes_apontam_para_routers_dos_apps(self):
        self.assertEqual(resolve('/api/').url_name, 'smart-rh-api-root')
        self.assertEqual(resolve('/api/setor/setores/').url_name, 'setor-list')
        self.assertEqual(resolve('/api/funcionario/funcionarios/').url_name, 'funcionario-list')
        self.assertEqual(resolve('/api/avaliacao/avaliacoes-desempenho/').url_name, 'avaliacao-desempenho-list')
        self.assertEqual(resolve('/api/candidato/vagas/').url_name, 'vaga-list')

    def test_apps_nao_ficam_expostas_fora_do_prefixo_api(self):
        for path in ['/setor/setores/', '/funcionario/funcionarios/', '/avaliacao/avaliacoes-desempenho/', '/candidato/vagas/']:
            with self.subTest(path=path):
                with self.assertRaises(Resolver404):
                    resolve(path)

    def test_drf_spectacular_docs_sao_condicionais(self):
        response = self.client.get('/api/')
        data = response.json()
        spectacular_available = bool(find_spec('drf_spectacular'))

        self.assertEqual(data['documentation_enabled'], spectacular_available)

        if spectacular_available:
            self.assertEqual(resolve('/api/schema/').url_name, 'api-schema')
            self.assertEqual(resolve('/api/docs/').url_name, 'api-docs')
            self.assertEqual(resolve('/api/redoc/').url_name, 'api-redoc')
            self.assertIn('/api/schema/', data['documentation']['schema'])
            return

        self.assertIsNone(data['documentation']['schema'])
        with self.assertRaises(Resolver404):
            resolve('/api/schema/')
