from decimal import Decimal
from unittest.mock import Mock, patch

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework import permissions, viewsets

from apps.api_mixins import RHAdminModelViewSetMixin
from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AnaliseComportamentalWriteSerializer,
    AvaliacaoDesempenhoReadSerializer,
    AvaliacaoDesempenhoWriteSerializer,
)
from apps.avaliacao.api.test_views import avaliacao_test_page
from apps.avaliacao.api.views import AnaliseComportamentalViewSet, AvaliacaoDesempenhoViewSet


class AvaliacaoCRUDViewSetTests(SimpleTestCase):
    def test_viewsets_usam_model_viewset_para_crud_completo(self):
        self.assertTrue(issubclass(AnaliseComportamentalViewSet, viewsets.ModelViewSet))
        self.assertTrue(issubclass(AvaliacaoDesempenhoViewSet, viewsets.ModelViewSet))

    def test_rotas_crud_resolvem_sob_prefixo_api(self):
        expected_routes = {
            '/api/avaliacao/analises-comportamentais/': 'analise-comportamental-list',
            '/api/avaliacao/analises-comportamentais/1/': 'analise-comportamental-detail',
            '/api/avaliacao/avaliacoes-desempenho/': 'avaliacao-desempenho-list',
            '/api/avaliacao/avaliacoes-desempenho/1/': 'avaliacao-desempenho-detail',
        }

        for path, url_name in expected_routes.items():
            with self.subTest(path=path):
                self.assertEqual(resolve(path).url_name, url_name)

    def test_viewsets_usam_serializer_de_escrita_em_acoes_de_crud(self):
        expected_serializers = {
            AnaliseComportamentalViewSet: (
                AnaliseComportamentalReadSerializer,
                AnaliseComportamentalWriteSerializer,
            ),
            AvaliacaoDesempenhoViewSet: (
                AvaliacaoDesempenhoReadSerializer,
                AvaliacaoDesempenhoWriteSerializer,
            ),
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
        for viewset_class in [AnaliseComportamentalViewSet, AvaliacaoDesempenhoViewSet]:
            with self.subTest(viewset=viewset_class.__name__):
                self.assertTrue(issubclass(viewset_class, RHAdminModelViewSetMixin))
                self.assertEqual(viewset_class.permission_classes, [permissions.IsAuthenticated])

    def test_indicadores_calculam_media_sobre_queryset_filtrado(self):
        viewset = AvaliacaoDesempenhoViewSet()
        request = RequestFactory().get(
            '/api/avaliacao/avaliacoes-desempenho/rh/indicadores/',
            {
                'data_avaliacao_de': '2026-01-01',
                'data_avaliacao_ate': '2026-01-31',
            },
        )
        queryset = Mock(name='base_queryset')
        filtered_queryset = Mock(name='filtered_queryset')
        filtered_queryset.count.return_value = 2
        filtered_queryset.aggregate.return_value = {'media_nota': Decimal('8.25')}
        viewset.request = request
        viewset.get_queryset = Mock(return_value=queryset)
        viewset.filter_queryset = Mock(return_value=filtered_queryset)
        viewset.assert_rh_admin_access = Mock()

        with patch('apps.avaliacao.api.views.AnaliseComportamental.objects.count', return_value=5):
            response = viewset.rh_indicadores(request)

        viewset.assert_rh_admin_access.assert_called_once_with()
        viewset.get_queryset.assert_called_once_with()
        viewset.filter_queryset.assert_called_once_with(queryset)
        filtered_queryset.aggregate.assert_called_once()
        filtered_queryset.count.assert_called_once_with()
        self.assertEqual(response.data['total_avaliacoes_desempenho'], 2)
        self.assertEqual(response.data['total_analises_comportamentais'], 5)
        self.assertEqual(response.data['media_nota_avaliacoes_desempenho'], 8.25)

    def test_indicadores_retornam_media_nula_sem_notas(self):
        viewset = AvaliacaoDesempenhoViewSet()
        request = RequestFactory().get('/api/avaliacao/avaliacoes-desempenho/rh/indicadores/')
        queryset = Mock(name='base_queryset')
        filtered_queryset = Mock(name='filtered_queryset')
        filtered_queryset.count.return_value = 0
        filtered_queryset.aggregate.return_value = {'media_nota': None}
        viewset.request = request
        viewset.get_queryset = Mock(return_value=queryset)
        viewset.filter_queryset = Mock(return_value=filtered_queryset)
        viewset.assert_rh_admin_access = Mock()

        with patch('apps.avaliacao.api.views.AnaliseComportamental.objects.count', return_value=0):
            response = viewset.rh_indicadores(request)

        self.assertIsNone(response.data['media_nota_avaliacoes_desempenho'])


class AvaliacaoTestPageTests(SimpleTestCase):
    def test_rota_tela_teste_avaliacao_existe(self):
        match = resolve('/api/avaliacao/teste/')

        self.assertEqual(match.url_name, 'avaliacao-teste-page')

    @override_settings(DEBUG=True)
    def test_tela_teste_renderiza_forms_tabelas_e_botoes(self):
        request = RequestFactory().get('/api/avaliacao/teste/')

        response = avaliacao_test_page(request)
        content = response.content.decode('utf-8')

        self.assertIn('<form id="evaluation-form">', content)
        self.assertIn('<form id="analysis-form">', content)
        self.assertIn('<tbody id="employees-body"></tbody>', content)
        self.assertIn('<tbody id="evaluations-body"></tbody>', content)
        self.assertIn('<tbody id="analyses-body"></tbody>', content)
        self.assertIn('Editar', content)
        self.assertIn('Deletar', content)

    @override_settings(DEBUG=False)
    def test_tela_teste_fica_indisponivel_fora_de_debug(self):
        request = RequestFactory().get('/api/avaliacao/teste/')

        with self.assertRaises(Http404):
            avaliacao_test_page(request)
