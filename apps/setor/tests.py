from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework import permissions, viewsets

from apps.api_mixins import RHAdminModelViewSetMixin
from apps.setor.api.serializers import (
    CargoReadSerializer,
    CargoWriteSerializer,
    SetorReadSerializer,
    SetorWriteSerializer,
)
from apps.setor.api.test_views import setor_test_page
from apps.setor.api.views import CargoViewSet, SetorViewSet


class SetorCargoCRUDViewSetTests(SimpleTestCase):
    def test_viewsets_usam_model_viewset_para_crud_completo(self):
        self.assertTrue(issubclass(SetorViewSet, viewsets.ModelViewSet))
        self.assertTrue(issubclass(CargoViewSet, viewsets.ModelViewSet))

    def test_rotas_crud_resolvem_sob_prefixo_api(self):
        expected_routes = {
            '/api/setor/setores/': 'setor-list',
            '/api/setor/setores/1/': 'setor-detail',
            '/api/setor/cargos/': 'cargo-list',
            '/api/setor/cargos/1/': 'cargo-detail',
        }

        for path, url_name in expected_routes.items():
            with self.subTest(path=path):
                self.assertEqual(resolve(path).url_name, url_name)

    def test_rotas_funcionarios_por_setor_cargo_e_estatisticas_resolvem(self):
        expected_routes = {
            '/api/setor/setores/1/funcionarios/': 'setor-funcionarios',
            '/api/setor/cargos/1/funcionarios/': 'cargo-funcionarios',
            '/api/setor/setores/rh/indicadores/': 'setor-rh-indicadores',
        }

        for path, url_name in expected_routes.items():
            with self.subTest(path=path):
                self.assertEqual(resolve(path).url_name, url_name)

    def test_viewsets_usam_serializer_de_escrita_em_acoes_de_crud(self):
        expected_serializers = {
            SetorViewSet: (SetorReadSerializer, SetorWriteSerializer),
            CargoViewSet: (CargoReadSerializer, CargoWriteSerializer),
        }

        for viewset_class, (read_serializer, write_serializer) in expected_serializers.items():
            with self.subTest(viewset=viewset_class.__name__):
                viewset = viewset_class()
                viewset.action = 'list'
                self.assertIs(viewset.get_serializer_class(), read_serializer)

                for action in ['create', 'update', 'partial_update', 'destroy']:
                    viewset.action = action
                    self.assertIs(viewset.get_serializer_class(), write_serializer)

    def test_viewsets_exigem_autenticacao_e_mixin_rh_admin_para_escrita(self):
        for viewset_class in [SetorViewSet, CargoViewSet]:
            with self.subTest(viewset=viewset_class.__name__):
                self.assertTrue(issubclass(viewset_class, RHAdminModelViewSetMixin))
                self.assertEqual(viewset_class.permission_classes, [permissions.IsAuthenticated])


class SetorCargoTestPageTests(SimpleTestCase):
    def test_rota_tela_teste_setor_cargo_existe(self):
        match = resolve('/api/setor/teste/')

        self.assertEqual(match.url_name, 'setor-teste-page')

    @override_settings(DEBUG=True)
    def test_tela_teste_renderiza_forms_tabelas_e_botoes(self):
        request = RequestFactory().get('/api/setor/teste/')

        response = setor_test_page(request)
        content = response.content.decode('utf-8')

        self.assertIn('<form id="sector-form">', content)
        self.assertIn('<form id="role-form">', content)
        self.assertIn('<tbody id="sectors-body"></tbody>', content)
        self.assertIn('<tbody id="roles-body"></tbody>', content)
        self.assertIn('Editar', content)
        self.assertIn('Deletar', content)

    @override_settings(DEBUG=False)
    def test_tela_teste_fica_indisponivel_fora_de_debug(self):
        request = RequestFactory().get('/api/setor/teste/')

        with self.assertRaises(Http404):
            setor_test_page(request)
