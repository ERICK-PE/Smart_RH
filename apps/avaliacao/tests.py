from contextlib import nullcontext
from decimal import Decimal
from datetime import datetime, timezone as datetime_timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework import permissions, viewsets

from apps.api_mixins import RHAdminModelViewSetMixin
from apps.avaliacao.api.serializers import (
    ANALISE_COMPORTAMENTAL_PERGUNTAS,
    AnaliseComportamentalReadSerializer,
    AnaliseComportamentalRespostaSubmitSerializer,
    AnaliseComportamentalWriteSerializer,
    AvaliacaoDesempenhoReadSerializer,
    AvaliacaoDesempenhoWriteSerializer,
)
from apps.avaliacao.api.test_views import avaliacao_test_page
from apps.avaliacao.api.views import AnaliseComportamentalViewSet, AvaliacaoDesempenhoViewSet
from apps.avaliacao.services.analise_comportamental_ia import (
    build_behavioral_analysis_task_prompt,
    generate_behavioral_analysis_report,
)


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

    def test_rotas_formulario_analise_comportamental_resolvem_sob_prefixo_api(self):
        expected_routes = {
            '/api/avaliacao/analises-comportamentais/enviar/': 'analise-comportamental-enviar',
            '/api/avaliacao/analises-comportamentais/pendentes/': 'analise-comportamental-pendentes',
            '/api/avaliacao/analises-comportamentais/respostas/1/responder/': 'analise-comportamental-responder',
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

    def test_formulario_analise_comportamental_rejeita_resposta_obrigatoria_ausente(self):
        respostas = {
            question['id']: (question.get('opcoes') or ['teste'])[0]
            for question in ANALISE_COMPORTAMENTAL_PERGUNTAS
            if question.get('obrigatoria') is not False
        }
        respostas.pop('sentimento')

        serializer = AnaliseComportamentalRespostaSubmitSerializer(data={'respostas': respostas})

        self.assertFalse(serializer.is_valid())
        self.assertIn('sentimento', str(serializer.errors))

    def test_formulario_analise_comportamental_rejeita_opcao_invalida(self):
        respostas = {
            question['id']: (question.get('opcoes') or ['teste'])[0]
            for question in ANALISE_COMPORTAMENTAL_PERGUNTAS
            if question.get('obrigatoria') is not False
        }
        respostas['sentimento'] = 'Opcao inexistente'

        serializer = AnaliseComportamentalRespostaSubmitSerializer(data={'respostas': respostas})

        self.assertFalse(serializer.is_valid())
        self.assertIn('sentimento', str(serializer.errors))

    def test_formulario_analise_comportamental_aceita_respostas_validas(self):
        respostas = {
            question['id']: (question.get('opcoes') or ['teste'])[0]
            for question in ANALISE_COMPORTAMENTAL_PERGUNTAS
            if question.get('obrigatoria') is not False
        }

        serializer = AnaliseComportamentalRespostaSubmitSerializer(data={'respostas': respostas})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_prompt_da_ia_usa_nome_setor_data_e_respostas(self):
        funcionario = SimpleNamespace(nome='Teste Funcionario', fk_id_setor=SimpleNamespace(nome='Tecnologia'))
        resposta = SimpleNamespace(
            fk_id_funcionario=funcionario,
            respondido_em=datetime(2026, 7, 8, tzinfo=datetime_timezone.utc),
        )
        respostas = {
            'sentimento': 'Feliz',
            'sentimento_observacao': 'Bom clima.',
            'desenvolvimento_profissional': 'Sempre',
            'reconhecimento': 'Valorizado',
            'ambiente_fisico': '4',
            'clima_geral': '5',
            'lideranca_empresa': 'Apoiador',
            'relacao_colegas': '5',
        }

        prompt = build_behavioral_analysis_task_prompt(resposta, respostas)

        self.assertIn('Identificador: Teste Funcionario', prompt)
        self.assertIn('Setor: Tecnologia', prompt)
        self.assertIn('Data da resposta: 08/07/2026', prompt)
        self.assertIn('Termômetro de sentimento: Feliz', prompt)
        self.assertIn('Observação aberta: Bom clima.', prompt)

    def test_agente_ia_chama_openai_com_prompt_comportamental(self):
        funcionario = SimpleNamespace(nome='Teste Funcionario', fk_id_setor=SimpleNamespace(nome='Tecnologia'))
        resposta = SimpleNamespace(
            fk_id_funcionario=funcionario,
            respondido_em=datetime(2026, 7, 8, tzinfo=datetime_timezone.utc),
        )
        respostas = {
            question['id']: (question.get('opcoes') or ['teste'])[0]
            for question in ANALISE_COMPORTAMENTAL_PERGUNTAS
            if question.get('obrigatoria') is not False
        }
        mock_client = Mock()
        mock_client.responses.create.return_value = SimpleNamespace(output_text='Relatorio comportamental IA')

        with (
            patch.dict('os.environ', {'OPEN_API_KEY': 'test-key'}),
            patch('apps.avaliacao.services.analise_comportamental_ia.OpenAI', return_value=mock_client) as openai_mock,
        ):
            relatorio = generate_behavioral_analysis_report(resposta, respostas)

        openai_mock.assert_called_once_with(api_key='test-key', timeout=30.0)
        request_payload = mock_client.responses.create.call_args.kwargs
        self.assertIn('análise de clima organizacional', request_payload['input'][0]['content'])
        self.assertIn('Teste Funcionario', request_payload['input'][1]['content'])
        self.assertEqual(relatorio, 'Relatorio comportamental IA')

    def test_submit_serializer_grava_resultado_com_relatorio_da_ia(self):
        respostas = {
            question['id']: (question.get('opcoes') or ['teste'])[0]
            for question in ANALISE_COMPORTAMENTAL_PERGUNTAS
            if question.get('obrigatoria') is not False
        }
        resposta = Mock()
        resposta.fk_id_funcionario = Mock()
        serializer = AnaliseComportamentalRespostaSubmitSerializer(
            data={'respostas': respostas},
            context={'resposta': resposta},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with (
            patch(
                'apps.avaliacao.services.analise_comportamental_ia.generate_behavioral_analysis_report',
                return_value='Relatorio final da IA',
            ) as ia_mock,
            patch('apps.avaliacao.api.serializers.AnaliseComportamental.objects.create') as create_mock,
            patch('apps.avaliacao.api.serializers.transaction.atomic', return_value=nullcontext()),
        ):
            serializer.save()

        ia_mock.assert_called_once()
        resposta.save.assert_called_once_with(update_fields=['respostas', 'status', 'respondido_em'])
        create_mock.assert_called_once()
        self.assertEqual(create_mock.call_args.kwargs['resultado'], 'Relatorio final da IA')


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
