from django.test import SimpleTestCase
from django.urls import resolve
from rest_framework.test import APIClient
from rest_framework import permissions, viewsets

from apps.api_mixins import RHAdminModelViewSetMixin
from apps.avaliacao.api.views import (
    AnaliseComportamentalViewSet,
    AvaliacaoDesempenhoViewSet,
)
from apps.candidato_vaga.api.views import CandidatoVagaViewSet, CandidatoViewSet, VagaViewSet
from apps.funcionario.api.views import (
    ContratoViewSet,
    FolhaPagamentoViewSet,
    FuncionarioAgenteDocumentoViewSet,
    FuncionarioViewSet,
    PlanoCarreiraViewSet,
)
from apps.setor.api.views import CargoViewSet, SetorViewSet


class APIEndpointContractTests(SimpleTestCase):
    list_crud_routes = [
        '/api/setor/setores/',
        '/api/setor/cargos/',
        '/api/funcionario/funcionarios/',
        '/api/funcionario/planos-carreira/',
        '/api/funcionario/contratos/',
        '/api/funcionario/folhas-pagamento/',
        '/api/funcionario/agente/',
        '/api/candidato/candidatos/',
        '/api/candidato/vagas/',
        '/api/candidato/candidato-vagas/',
        '/api/avaliacao/analises-comportamentais/',
        '/api/avaliacao/avaliacoes-desempenho/',
    ]
    detail_crud_routes = [
        '/api/setor/setores/1/',
        '/api/setor/cargos/1/',
        '/api/funcionario/funcionarios/1/',
        '/api/funcionario/planos-carreira/1/',
        '/api/funcionario/contratos/1/',
        '/api/funcionario/folhas-pagamento/1/',
        '/api/funcionario/agente/1/',
        '/api/candidato/candidatos/12345678901/',
        '/api/candidato/vagas/1/',
        '/api/candidato/candidato-vagas/12345678901:1/',
        '/api/avaliacao/analises-comportamentais/1/',
        '/api/avaliacao/avaliacoes-desempenho/1/',
    ]
    authenticated_viewsets = [
        SetorViewSet,
        CargoViewSet,
        FuncionarioViewSet,
        PlanoCarreiraViewSet,
        ContratoViewSet,
        FolhaPagamentoViewSet,
        FuncionarioAgenteDocumentoViewSet,
        CandidatoViewSet,
        VagaViewSet,
        CandidatoVagaViewSet,
        AnaliseComportamentalViewSet,
        AvaliacaoDesempenhoViewSet,
    ]
    rh_admin_write_viewsets = [
        SetorViewSet,
        CargoViewSet,
        FuncionarioViewSet,
        PlanoCarreiraViewSet,
        ContratoViewSet,
        FolhaPagamentoViewSet,
        FuncionarioAgenteDocumentoViewSet,
        VagaViewSet,
        CandidatoVagaViewSet,
        AnaliseComportamentalViewSet,
        AvaliacaoDesempenhoViewSet,
    ]

    def test_rotas_list_expoem_get_e_post(self):
        expected_actions = {'get': 'list', 'post': 'create'}

        for path in self.list_crud_routes:
            with self.subTest(path=path):
                match = resolve(path)

                for method, action in expected_actions.items():
                    self.assertEqual(match.func.actions[method], action)

    def test_rotas_detail_expoem_get_put_patch_e_delete(self):
        expected_actions = {
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }

        for path in self.detail_crud_routes:
            with self.subTest(path=path):
                match = resolve(path)

                for method, action in expected_actions.items():
                    self.assertEqual(match.func.actions[method], action)

    def test_viewsets_crud_exigem_autenticacao(self):
        for viewset_class in self.authenticated_viewsets:
            with self.subTest(viewset=viewset_class.__name__):
                self.assertIn(permissions.IsAuthenticated, viewset_class.permission_classes)

    def test_metodos_crud_bloqueiam_usuario_anonimo(self):
        client = APIClient()
        route_methods = [
            *[(path, ['get', 'post']) for path in self.list_crud_routes],
            *[(path, ['get', 'put', 'patch', 'delete']) for path in self.detail_crud_routes],
        ]

        for path, methods in route_methods:
            for method in methods:
                with self.subTest(path=path, method=method):
                    request = getattr(client, method)
                    response = request(path, {}, format='json')

                    self.assertIn(response.status_code, [401, 403])

    def test_escrita_administrativa_usa_mixin_rh_admin(self):
        for viewset_class in self.rh_admin_write_viewsets:
            with self.subTest(viewset=viewset_class.__name__):
                self.assertTrue(issubclass(viewset_class, viewsets.ModelViewSet))
                self.assertTrue(issubclass(viewset_class, RHAdminModelViewSetMixin))

    def test_candidato_tem_politica_propria_para_escrita(self):
        self.assertTrue(issubclass(CandidatoViewSet, viewsets.ModelViewSet))
        self.assertFalse(issubclass(CandidatoViewSet, RHAdminModelViewSetMixin))
        self.assertEqual(
            CandidatoViewSet.candidate_self_write_actions,
            {'create', 'update', 'partial_update'},
        )
