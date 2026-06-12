from django.conf import settings
from django.test import SimpleTestCase
from rest_framework import viewsets

from apps.avaliacao.api.filters import AnaliseComportamentalFilter, AvaliacaoDesempenhoFilter
from apps.avaliacao.api.views import AnaliseComportamentalViewSet, AvaliacaoDesempenhoViewSet
from apps.candidato_vaga.api.filters import CandidatoFilter, CandidatoVagaFilter, VagaFilter
from apps.candidato_vaga.api.views import CandidatoVagaViewSet, CandidatoViewSet, VagaViewSet
from apps.funcionario.api.filters import ContratoFilter, FuncionarioFilter, PlanoCarreiraFilter
from apps.funcionario.api.views import ContratoViewSet, FuncionarioViewSet, PlanoCarreiraViewSet
from apps.setor.api.filters import CargoFilter, SetorFilter
from apps.setor.api.views import CargoViewSet, SetorViewSet


class APIFilterConfigurationTests(SimpleTestCase):
    def test_rest_framework_usa_django_filter_e_search_filter(self):
        filter_backends = settings.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS']

        self.assertIn('django_filters.rest_framework.DjangoFilterBackend', filter_backends)
        self.assertIn('rest_framework.filters.SearchFilter', filter_backends)

    def test_rest_framework_usa_session_authentication(self):
        authentication_classes = settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']

        self.assertEqual(authentication_classes, ['rest_framework.authentication.SessionAuthentication'])

    def test_funcionario_crud_usa_model_viewset(self):
        self.assertTrue(issubclass(FuncionarioViewSet, viewsets.ModelViewSet))
        self.assertIn('status', FuncionarioViewSet.filterset_fields)

    def test_viewsets_possuem_filterset_fields_e_search_fields(self):
        viewsets = [
            SetorViewSet,
            CargoViewSet,
            FuncionarioViewSet,
            PlanoCarreiraViewSet,
            ContratoViewSet,
            CandidatoViewSet,
            VagaViewSet,
            CandidatoVagaViewSet,
            AnaliseComportamentalViewSet,
            AvaliacaoDesempenhoViewSet,
        ]

        for viewset in viewsets:
            with self.subTest(viewset=viewset.__name__):
                self.assertTrue(viewset.filterset_fields)
                self.assertTrue(viewset.search_fields)

    def test_viewsets_usam_filtersets_customizados(self):
        expected_filtersets = {
            SetorViewSet: SetorFilter,
            CargoViewSet: CargoFilter,
            FuncionarioViewSet: FuncionarioFilter,
            PlanoCarreiraViewSet: PlanoCarreiraFilter,
            ContratoViewSet: ContratoFilter,
            CandidatoViewSet: CandidatoFilter,
            VagaViewSet: VagaFilter,
            CandidatoVagaViewSet: CandidatoVagaFilter,
            AnaliseComportamentalViewSet: AnaliseComportamentalFilter,
            AvaliacaoDesempenhoViewSet: AvaliacaoDesempenhoFilter,
        }

        for viewset, filterset in expected_filtersets.items():
            with self.subTest(viewset=viewset.__name__):
                self.assertIs(viewset.filterset_class, filterset)

    def test_filtros_customizados_estao_registrados(self):
        expected_filters = {
            SetorFilter: {'possui_funcionarios', 'possui_vagas'},
            CargoFilter: {'possui_funcionarios', 'possui_planos_carreira'},
            FuncionarioFilter: {'status', 'setor_nome', 'cargo_nome', 'data_admissao_inicio', 'data_admissao_fim'},
            PlanoCarreiraFilter: {'texto', 'cargo_nome'},
            ContratoFilter: {'funcionario_nome', 'data_inicio_de', 'data_inicio_ate'},
            CandidatoFilter: {'possui_curriculo'},
            VagaFilter: {'texto', 'setor_nome', 'com_candidaturas'},
            CandidatoVagaFilter: {'candidato_nome', 'vaga_titulo'},
            AnaliseComportamentalFilter: {'funcionario_nome', 'data_analise_de', 'data_analise_ate'},
            AvaliacaoDesempenhoFilter: {'avaliador_nome', 'nota_min', 'nota_max', 'data_avaliacao_de', 'data_avaliacao_ate'},
        }

        for filterset, filters in expected_filters.items():
            with self.subTest(filterset=filterset.__name__):
                self.assertTrue(filters.issubset(filterset.base_filters))
