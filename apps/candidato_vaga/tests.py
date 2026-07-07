import importlib
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.parsers import MultiPartParser
from rest_framework import serializers, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.candidato_vaga.api.serializers import (
    CandidaturaCreateSerializer,
    CandidatoRegistrationSerializer,
    CandidatoReadSerializer,
    CandidatoVagaEmailSerializer,
    CandidatoVagaRHReadSerializer,
    CandidatoVagaReadSerializer,
    CandidatoVagaWriteSerializer,
    CandidatoWriteSerializer,
    VagaReadSerializer,
    VagaWriteSerializer,
)
from apps.candidato_vaga.api.filters import CandidatoVagaFilter, CandidatoVagaRHFilter
from apps.candidato_vaga.api.test_views import candidato_vaga_test_page
from apps.candidato_vaga.api.views import CandidatoAccessMixin, CandidatoVagaViewSet, CandidatoViewSet, VagaViewSet
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga, candidato_curriculo_upload_path
from apps.candidato_vaga.services.triagem_candidatura import (
    TRIAGEM_CLASSIFICACAO_APROVADO,
    TRIAGEM_CLASSIFICACAO_PENDENTE,
    TRIAGEM_CLASSIFICACAO_REPROVADO_TECNICO,
    TriagemCandidaturaResult,
    analisar_candidatura,
    extract_requirement_keywords,
)


class CandidatoWriteSerializerTests(SimpleTestCase):
    def test_cpf_duplicado_e_rejeitado(self):
        serializer = CandidatoWriteSerializer()

        with patch('apps.candidato_vaga.api.serializers.Candidato.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = True

            with self.assertRaises(serializers.ValidationError):
                serializer.validate_cpf_candidato('12345678901')

    def test_curriculo_aceita_pdf_doc_e_docx(self):
        candidato = Candidato(cpf_candidato='12345678901')

        arquivos = [
            ('curriculo.pdf', 'application/pdf'),
            ('curriculo.doc', 'application/msword'),
            (
                'curriculo.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ),
        ]

        for filename, content_type in arquivos:
            with self.subTest(filename=filename):
                serializer = CandidatoWriteSerializer(
                    candidato,
                    data={
                        'curriculo': SimpleUploadedFile(
                            filename,
                            b'conteudo',
                            content_type=content_type,
                        )
                    },
                    partial=True,
                )

                self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_curriculo_rejeita_extensao_invalida(self):
        serializer = CandidatoWriteSerializer(
            Candidato(cpf_candidato='12345678901'),
            data={
                'curriculo': SimpleUploadedFile(
                    'curriculo.exe',
                    b'conteudo',
                    content_type='application/octet-stream',
                )
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('curriculo', serializer.errors)

    def test_curriculo_rejeita_tipo_invalido_mesmo_com_extensao_valida(self):
        serializer = CandidatoWriteSerializer(
            Candidato(cpf_candidato='12345678901'),
            data={
                'curriculo': SimpleUploadedFile(
                    'curriculo.pdf',
                    b'conteudo',
                    content_type='text/plain',
                )
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('curriculo', serializer.errors)

    def test_curriculo_rejeita_arquivo_maior_que_5mb(self):
        serializer = CandidatoWriteSerializer(
            Candidato(cpf_candidato='12345678901'),
            data={
                'curriculo': SimpleUploadedFile(
                    'curriculo.pdf',
                    b'0' * ((5 * 1024 * 1024) + 1),
                    content_type='application/pdf',
                )
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('curriculo', serializer.errors)

    def test_curriculo_upload_path_usa_nome_original_sanitizado_sem_cpf(self):
        candidato = Candidato(cpf_candidato='123.456.789-01')

        path = candidato_curriculo_upload_path(candidato, 'Meu Curriculo Pessoal.PDF')

        self.assertEqual(path, 'curriculos/Meu_Curriculo_Pessoal.pdf')
        self.assertNotIn('12345678901', path)

    def test_curriculo_upload_path_remove_diretorios_do_nome_original(self):
        candidato = Candidato(cpf_candidato='12345678901')

        path = candidato_curriculo_upload_path(candidato, '../../curriculo final.docx')

        self.assertEqual(path, 'curriculos/curriculo_final.docx')


class CandidatoReadSerializerTests(SimpleTestCase):
    def test_curriculo_retorna_caminho_para_contexto_privilegiado(self):
        candidato = Candidato(
            cpf_candidato='12345678901',
            curriculo='curriculos/12345678901.pdf',
        )
        request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=True,
                is_superuser=False,
            )
        )

        data = CandidatoReadSerializer(candidato, context={'request': request}).data

        self.assertEqual(data['curriculo'], 'curriculos/12345678901.pdf')


class CandidatoRegistrationSerializerTests(SimpleTestCase):
    def test_password_e_write_only(self):
        serializer = CandidatoRegistrationSerializer()

        self.assertTrue(serializer.fields['password'].write_only)

    def test_registro_rejeita_username_duplicado_entre_candidatos(self):
        serializer = CandidatoRegistrationSerializer()

        with patch('apps.candidato_vaga.api.serializers.Candidato.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = True

            with self.assertRaises(serializers.ValidationError):
                serializer.validate_username('joao')

    def test_registro_permite_username_existente_fora_de_candidato(self):
        serializer = CandidatoRegistrationSerializer()

        with patch('apps.candidato_vaga.api.serializers.Candidato.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = False

            self.assertEqual(serializer.validate_username('joao'), 'joao')

    def test_registro_rejeita_email_duplicado_entre_candidatos(self):
        serializer = CandidatoRegistrationSerializer()

        with patch('apps.candidato_vaga.api.serializers.Candidato.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = True

            with self.assertRaises(serializers.ValidationError) as context:
                serializer.validate({
                    'username': 'joao',
                    'password': 'SenhaForte123',
                    'cpf_candidato': '12345678901',
                    'email': 'joao@example.com',
                })

        self.assertIn('email', context.exception.detail)

    def test_registro_rejeita_cpf_duplicado(self):
        serializer = CandidatoRegistrationSerializer()

        with patch('apps.candidato_vaga.api.serializers.Candidato.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = True

            with self.assertRaises(serializers.ValidationError):
                serializer.validate_cpf_candidato('12345678901')

    def test_registro_cria_user_e_candidato_vinculado(self):
        serializer = CandidatoRegistrationSerializer()
        user = SimpleNamespace(pk=10)
        create_user = Mock(return_value=user)
        user_model = Mock()
        user_model.USERNAME_FIELD = 'username'
        user_model._meta.get_field.return_value = SimpleNamespace(max_length=150)
        user_model.objects.create_user = create_user

        with patch('apps.candidato_vaga.api.serializers.get_user_model', return_value=user_model):
            with patch('apps.candidato_vaga.api.serializers.transaction.atomic', return_value=nullcontext()):
                with patch('apps.candidato_vaga.api.serializers.Candidato.objects.create') as create_candidato:
                    serializer.create({
                        'username': 'joao',
                        'password': 'SenhaForte123',
                        'cpf_candidato': '12345678901',
                        'nome': 'Joao',
                        'email': 'joao@example.com',
                    })

        create_user.assert_called_once_with(
            username='candidato:joao',
            email='joao@example.com',
            password='SenhaForte123',
        )
        create_candidato.assert_called_once_with(
            user=user,
            cpf_candidato='12345678901',
            nome='Joao',
            email='joao@example.com',
        )


class CandidatoVagaWriteSerializerTests(SimpleTestCase):
    def test_vinculo_duplicado_e_rejeitado(self):
        serializer = CandidatoVagaWriteSerializer()
        candidato = Candidato(cpf_candidato='12345678901')
        vaga = Vaga(id_vaga=1)

        with patch('apps.candidato_vaga.api.serializers.CandidatoVaga.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = True

            with self.assertRaises(serializers.ValidationError) as context:
                serializer.validate({
                    'cpf_candidato': candidato,
                    'id_vaga': vaga,
                })

        self.assertIn('id_vaga', context.exception.detail)


class VagaWriteSerializerTests(SimpleTestCase):
    def test_status_aceita_apenas_valores_validos(self):
        serializer = VagaWriteSerializer()

        self.assertEqual(serializer.validate_status('ABERTA'), Vaga.STATUS_ABERTA)
        self.assertEqual(serializer.validate_status('andamento'), Vaga.STATUS_ANDAMENTO)

        with self.assertRaises(serializers.ValidationError):
            serializer.validate_status('publicada')

    def test_vaga_serializers_expoem_e_normalizam_requisitos(self):
        vaga = Vaga(id_vaga=1, titulo='Dev', requisitos='Python Django')

        self.assertIn('requisitos', VagaReadSerializer(vaga).data)

        serializer = VagaWriteSerializer(
            vaga,
            data={'requisitos': '  Python Django  '},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['requisitos'], 'Python Django')


class CandidatoVagaReadSerializerTests(SimpleTestCase):
    def test_read_serializer_expoe_status_da_vaga(self):
        candidatura = CandidatoVaga(
            cpf_candidato=Candidato(cpf_candidato='12345678901'),
            id_vaga=Vaga(id_vaga=1, status=Vaga.STATUS_FECHADA),
            status_processo='candidatado',
        )

        data = CandidatoVagaReadSerializer(candidatura).data

        self.assertEqual(data['status_vaga'], Vaga.STATUS_FECHADA)

    def test_read_serializer_comum_nao_expoe_triagem_automatica(self):
        candidatura = CandidatoVaga(
            cpf_candidato=Candidato(cpf_candidato='12345678901'),
            id_vaga=Vaga(id_vaga=1, status=Vaga.STATUS_ABERTA),
            status_processo='andamento',
            triagem_automatica_aprovada=False,
            triagem_automatica_motivo='faltou django',
            triagem_automatica_palavras_chave='python, django',
            triagem_automatica_pontuacao=33,
            triagem_automatica_classificacao=TRIAGEM_CLASSIFICACAO_REPROVADO_TECNICO,
        )

        data = CandidatoVagaReadSerializer(candidatura).data

        self.assertNotIn('triagem_automatica_aprovada', data)
        self.assertNotIn('triagem_automatica_motivo', data)
        self.assertNotIn('triagem_automatica_palavras_chave', data)
        self.assertNotIn('triagem_automatica_pontuacao', data)
        self.assertNotIn('triagem_automatica_classificacao', data)

    def test_read_serializer_rh_expoe_triagem_automatica(self):
        candidatura = CandidatoVaga(
            cpf_candidato=Candidato(cpf_candidato='12345678901'),
            id_vaga=Vaga(id_vaga=1, status=Vaga.STATUS_ABERTA),
            status_processo='andamento',
            triagem_automatica_aprovada=True,
            triagem_automatica_motivo='aprovado',
            triagem_automatica_palavras_chave='python, django',
            triagem_automatica_pontuacao=100,
            triagem_automatica_classificacao=TRIAGEM_CLASSIFICACAO_APROVADO,
        )

        data = CandidatoVagaRHReadSerializer(candidatura).data

        self.assertTrue(data['triagem_automatica_aprovada'])
        self.assertEqual(data['triagem_automatica_motivo'], 'aprovado')
        self.assertEqual(data['triagem_automatica_palavras_chave'], 'python, django')
        self.assertEqual(data['triagem_automatica_pontuacao'], 100)
        self.assertEqual(data['triagem_automatica_classificacao'], TRIAGEM_CLASSIFICACAO_APROVADO)


class TriagemCandidaturaTests(SimpleTestCase):
    def test_extrai_palavras_chave_dos_requisitos_da_vaga(self):
        vaga = Vaga(
            descricao='Texto comercial sem requisitos',
            requisitos='Requisitos minimos: Python, Django e SQL.',
        )

        self.assertEqual(extract_requirement_keywords(vaga), ['python', 'django', 'sql'])

    def test_extrai_requisitos_curtos_importantes_da_vaga(self):
        vaga = Vaga(requisitos='C#, C++, BI, UI e UX.')

        self.assertEqual(extract_requirement_keywords(vaga), ['c#', 'c++', 'bi', 'ui', 'ux'])

    def test_triagem_aprova_quando_curriculo_tem_keywords(self):
        candidato = Candidato(cpf_candidato='12345678901', curriculo='curriculos/ana.docx')
        vaga = Vaga(requisitos='Python Django SQL')

        with patch(
            'apps.candidato_vaga.services.triagem_candidatura.extract_curriculo_text',
            return_value='Experiencia com Python, Django e SQL.',
        ):
            result = analisar_candidatura(candidato, vaga)

        self.assertTrue(result.aprovado)
        self.assertEqual(result.pontuacao, 100)
        self.assertEqual(result.classificacao, TRIAGEM_CLASSIFICACAO_APROVADO)
        self.assertEqual(result.palavras_faltantes, [])

    def test_triagem_aprova_requisitos_curtos_importantes(self):
        candidato = Candidato(cpf_candidato='12345678901', curriculo='curriculos/ana.docx')
        vaga = Vaga(requisitos='C# C++ BI UI UX')

        with patch(
            'apps.candidato_vaga.services.triagem_candidatura.extract_curriculo_text',
            return_value='Experiencia com C#, C++, BI, UI e UX.',
        ):
            result = analisar_candidatura(candidato, vaga)

        self.assertTrue(result.aprovado)
        self.assertEqual(result.pontuacao, 100)
        self.assertEqual(result.palavras_encontradas, ['c#', 'c++', 'bi', 'ui', 'ux'])
        self.assertEqual(result.palavras_faltantes, [])

    def test_triagem_nao_considera_java_dentro_de_javascript(self):
        candidato = Candidato(cpf_candidato='12345678901', curriculo='curriculos/ana.docx')
        vaga = Vaga(requisitos='Java SQL')

        with patch(
            'apps.candidato_vaga.services.triagem_candidatura.extract_curriculo_text',
            return_value='Experiencia com JavaScript e SQL.',
        ):
            result = analisar_candidatura(candidato, vaga)

        self.assertFalse(result.aprovado)
        self.assertEqual(result.pontuacao, 50)
        self.assertEqual(result.classificacao, TRIAGEM_CLASSIFICACAO_PENDENTE)
        self.assertEqual(result.palavras_encontradas, ['sql'])
        self.assertEqual(result.palavras_faltantes, ['java'])

    def test_triagem_pendente_quando_curriculo_tem_pontuacao_intermediaria(self):
        candidato = Candidato(cpf_candidato='12345678901', curriculo='curriculos/ana.docx')
        vaga = Vaga(requisitos='Python Django SQL')

        with patch(
            'apps.candidato_vaga.services.triagem_candidatura.extract_curriculo_text',
            return_value='Experiencia com Python e SQL.',
        ):
            result = analisar_candidatura(candidato, vaga)

        self.assertFalse(result.aprovado)
        self.assertEqual(result.pontuacao, 67)
        self.assertEqual(result.classificacao, TRIAGEM_CLASSIFICACAO_PENDENTE)
        self.assertEqual(result.palavras_faltantes, ['django'])

    def test_triagem_reprovado_tecnico_quando_pontuacao_baixa(self):
        candidato = Candidato(cpf_candidato='12345678901', curriculo='curriculos/ana.docx')
        vaga = Vaga(requisitos='Python Django SQL')

        with patch(
            'apps.candidato_vaga.services.triagem_candidatura.extract_curriculo_text',
            return_value='Experiencia com Python.',
        ):
            result = analisar_candidatura(candidato, vaga)

        self.assertFalse(result.aprovado)
        self.assertEqual(result.pontuacao, 33)
        self.assertEqual(result.classificacao, TRIAGEM_CLASSIFICACAO_REPROVADO_TECNICO)
        self.assertEqual(result.palavras_faltantes, ['django', 'sql'])

    def test_triagem_pendente_vaga_sem_requisitos_descritos(self):
        result = analisar_candidatura(
            Candidato(cpf_candidato='12345678901'),
            Vaga(requisitos=''),
        )

        self.assertFalse(result.aprovado)
        self.assertIsNone(result.pontuacao)
        self.assertEqual(result.classificacao, TRIAGEM_CLASSIFICACAO_PENDENTE)
        self.assertEqual(result.palavras_chave, [])

    def test_triagem_pendente_candidato_sem_curriculo(self):
        result = analisar_candidatura(
            Candidato(cpf_candidato='12345678901'),
            Vaga(requisitos='Python'),
        )

        self.assertFalse(result.aprovado)
        self.assertIsNone(result.pontuacao)
        self.assertEqual(result.classificacao, TRIAGEM_CLASSIFICACAO_PENDENTE)
        self.assertEqual(result.palavras_faltantes, ['python'])


class CandidaturaCreateSerializerTests(SimpleTestCase):
    def test_candidatura_duplicada_e_rejeitada(self):
        serializer = CandidaturaCreateSerializer(context={
            'candidato': Candidato(cpf_candidato='12345678901'),
        })

        with patch('apps.candidato_vaga.api.serializers.CandidatoVaga.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = True

            with self.assertRaises(serializers.ValidationError) as context:
                serializer.validate({'id_vaga': Vaga(id_vaga=1)})

        self.assertIn('id_vaga', context.exception.detail)

    def test_candidatura_em_vaga_fechada_ou_cancelada_e_rejeitada(self):
        serializer = CandidaturaCreateSerializer(context={
            'candidato': Candidato(cpf_candidato='12345678901'),
        })

        with patch('apps.candidato_vaga.api.serializers.CandidatoVaga.objects.filter') as filter_mock:
            filter_mock.return_value.exists.return_value = False

            for status_vaga in [Vaga.STATUS_FECHADA, Vaga.STATUS_CANCELADA]:
                with self.subTest(status=status_vaga):
                    with self.assertRaises(serializers.ValidationError) as context:
                        serializer.validate({'id_vaga': Vaga(id_vaga=1, status=status_vaga)})

                    self.assertIn('id_vaga', context.exception.detail)

    def test_create_salva_triagem_e_status_andamento(self):
        candidato = Candidato(cpf_candidato='12345678901')
        vaga = Vaga(id_vaga=1, status=Vaga.STATUS_ABERTA)
        serializer = CandidaturaCreateSerializer(context={'candidato': candidato})
        triagem = TriagemCandidaturaResult(
            aprovado=True,
            motivo='aprovado',
            palavras_chave=['python', 'django'],
            palavras_encontradas=['python', 'django'],
            palavras_faltantes=[],
            pontuacao=100,
            classificacao=TRIAGEM_CLASSIFICACAO_APROVADO,
        )

        with patch('apps.candidato_vaga.api.serializers.analisar_candidatura', return_value=triagem):
            with patch('apps.candidato_vaga.api.serializers.CandidatoVaga.objects.create') as create_mock:
                serializer.create({'id_vaga': vaga})

        create_mock.assert_called_once_with(
            cpf_candidato=candidato,
            id_vaga=vaga,
            status_processo='andamento',
            triagem_automatica_aprovada=True,
            triagem_automatica_motivo='aprovado',
            triagem_automatica_palavras_chave='python, django',
            triagem_automatica_pontuacao=100,
            triagem_automatica_classificacao=TRIAGEM_CLASSIFICACAO_APROVADO,
        )


class CandidatoVagaViewSetTests(SimpleTestCase):
    def test_candidato_vaga_usa_crud_completo(self):
        self.assertTrue(issubclass(CandidatoViewSet, viewsets.ModelViewSet))
        self.assertTrue(issubclass(VagaViewSet, viewsets.ModelViewSet))
        self.assertTrue(issubclass(CandidatoVagaViewSet, viewsets.ModelViewSet))

    def test_candidato_viewset_aceita_multipart_para_curriculo(self):
        self.assertIn(MultiPartParser, CandidatoViewSet.parser_classes)

    def test_rota_atualizacao_processo_da_vaga_existe(self):
        match = resolve('/api/candidato/vagas/1/rh/processos/12345678901/')

        self.assertEqual(match.url_name, 'vaga-rh-atualizar-processo')

    def test_rota_atualizacao_status_da_vaga_existe(self):
        match = resolve('/api/candidato/vagas/1/rh/status/')

        self.assertEqual(match.url_name, 'vaga-rh-status')

    def test_rota_triagem_revisao_existe(self):
        match = resolve('/api/candidato/vagas/1/rh/triagem-revisao/')

        self.assertEqual(match.url_name, 'vaga-rh-triagem-revisao')

    def test_rota_envio_email_candidatos_existe(self):
        match = resolve('/api/candidato/vagas/1/rh/enviar-email-candidatos/')

        self.assertEqual(match.url_name, 'vaga-rh-enviar-email-candidatos')

    def test_rota_registro_publico_de_candidato_existe(self):
        match = resolve('/api/candidato/candidatos/registrar/')

        self.assertEqual(match.url_name, 'candidato-registrar')

    def test_rota_tela_teste_candidato_vaga_existe(self):
        match = resolve('/api/candidato/teste/')

        self.assertEqual(match.url_name, 'candidato-vaga-teste-page')

    def test_vagas_disponiveis_exclui_status_fechada_e_cancelada(self):
        candidato = Mock()
        candidato.candidatovaga_set.values_list.return_value = [3]
        vagas_elegiveis = Mock()
        vagas_nao_candidatadas = Mock()
        vagas_elegiveis.exclude.return_value = vagas_nao_candidatadas
        vagas_nao_candidatadas.order_by.return_value = 'vagas-disponiveis'

        viewset = CandidatoViewSet()
        viewset.get_candidato_object = Mock(return_value=candidato)
        viewset.paginated_serializer_response = Mock(return_value='response')

        with patch(
            'apps.candidato_vaga.api.views.Vaga.objects.filter',
            return_value=vagas_elegiveis,
        ) as filter_mock:
            response = viewset.vagas_disponiveis(SimpleNamespace(), pk='12345678901')

        filter_mock.assert_called_once_with(
            status__in=[Vaga.STATUS_ABERTA, Vaga.STATUS_ANDAMENTO],
        )
        vagas_elegiveis.exclude.assert_called_once_with(pk__in=[3])
        vagas_nao_candidatadas.order_by.assert_called_once_with('id_vaga')
        viewset.paginated_serializer_response.assert_called_once_with(
            'vagas-disponiveis',
            VagaReadSerializer,
        )
        self.assertEqual(response, 'response')

    def test_lookup_composto_usa_cpf_e_vaga(self):
        viewset = CandidatoVagaViewSet()

        self.assertEqual(
            viewset.parse_composite_lookup('12345678901:7'),
            ('12345678901', '7'),
        )

        with self.assertRaises(NotFound):
            viewset.parse_composite_lookup('12345678901')

    def test_filtro_comum_nao_usa_campos_internos_de_triagem(self):
        seen_filtersets = []

        class Backend:
            def filter_queryset(self, request, queryset, view):
                seen_filtersets.append(view.filterset_class)
                return queryset

        user = SimpleNamespace(is_authenticated=True, is_staff=False, is_superuser=False, pk=None)
        viewset = CandidatoVagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        viewset.filter_backends = [Backend]

        self.assertEqual(viewset.filter_queryset('queryset'), 'queryset')
        self.assertEqual(seen_filtersets, [CandidatoVagaFilter])
        self.assertNotIn('triagem_automatica_classificacao', viewset.get_search_fields(viewset.request))

    def test_filtro_rh_usa_campos_internos_de_triagem_e_restaura_estado(self):
        seen_filtersets = []

        class Backend:
            def filter_queryset(self, request, queryset, view):
                seen_filtersets.append(view.filterset_class)
                return queryset

        user = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        viewset = CandidatoVagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        viewset.filter_backends = [Backend]

        self.assertEqual(viewset.filter_queryset('queryset'), 'queryset')
        self.assertEqual(seen_filtersets, [CandidatoVagaRHFilter])
        self.assertEqual(viewset.filterset_class, CandidatoVagaFilter)
        self.assertIn('triagem_automatica_classificacao', viewset.get_search_fields(viewset.request))

    def test_indicadores_de_vagas_usam_queryset_filtrado(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        viewset = VagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        vagas_queryset = Mock()
        vagas_queryset.count.return_value = 2
        vagas_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {'status': Vaga.STATUS_ABERTA, 'total': 2},
        ]
        vagas_fechadas_queryset = Mock()
        vagas_visiveis_queryset = Mock()
        vagas_queryset.filter.side_effect = [
            vagas_fechadas_queryset,
            vagas_visiveis_queryset,
        ]
        candidaturas_queryset = Mock()
        candidaturas_queryset.count.return_value = 5
        candidaturas_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {'status_processo': 'candidatado', 'total': 5},
        ]
        candidaturas_fechadas_queryset = Mock()
        candidaturas_fechadas_queryset.count.return_value = 2
        candidaturas_fechadas_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {'status_processo': 'finalizado', 'total': 2},
        ]
        candidaturas_visiveis_queryset = Mock()
        candidaturas_visiveis_queryset.count.return_value = 3
        candidaturas_visiveis_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {'status_processo': 'triagem', 'total': 3},
        ]
        viewset.get_queryset = Mock(return_value='base-queryset')
        viewset.filter_queryset = Mock(return_value=vagas_queryset)

        with patch('apps.candidato_vaga.api.views.Candidato.objects.count', return_value=3):
            with patch(
                'apps.candidato_vaga.api.views.CandidatoVaga.objects.filter',
                side_effect=[
                    candidaturas_queryset,
                    candidaturas_fechadas_queryset,
                    candidaturas_visiveis_queryset,
                ],
            ) as candidatura_filter_mock:
                response = viewset.rh_indicadores(SimpleNamespace())

        viewset.filter_queryset.assert_called_once_with('base-queryset')
        vagas_queryset.filter.assert_any_call(status=Vaga.STATUS_FECHADA)
        vagas_queryset.filter.assert_any_call(
            status__in=[Vaga.STATUS_ABERTA, Vaga.STATUS_ANDAMENTO],
        )
        candidatura_filter_mock.assert_any_call(id_vaga__in=vagas_queryset)
        candidatura_filter_mock.assert_any_call(id_vaga__in=vagas_fechadas_queryset)
        candidatura_filter_mock.assert_any_call(id_vaga__in=vagas_visiveis_queryset)
        self.assertEqual(response.data['total_vagas'], 2)
        self.assertEqual(response.data['total_candidaturas'], 5)
        self.assertEqual(response.data['total_candidaturas_vagas_fechadas'], 2)
        self.assertEqual(response.data['total_candidaturas_vagas_visiveis'], 3)
        self.assertEqual(response.data['vagas_por_status'], {Vaga.STATUS_ABERTA: 2})
        self.assertEqual(response.data['candidaturas_por_status'], {'candidatado': 5})
        self.assertEqual(response.data['candidaturas_vagas_fechadas_por_status'], {'finalizado': 2})
        self.assertEqual(response.data['candidaturas_vagas_visiveis_por_status'], {'triagem': 3})

    def test_rh_candidatos_lista_apenas_aprovados_pela_triagem(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        approved_queryset = Mock()
        ordered_queryset = Mock()
        relation_queryset = Mock()
        relation_queryset.filter.return_value = approved_queryset
        approved_queryset.order_by.return_value = ordered_queryset
        vaga = SimpleNamespace(
            candidatovaga_set=SimpleNamespace(all=Mock(return_value=relation_queryset)),
        )
        viewset = VagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        viewset.get_object = Mock(return_value=vaga)
        viewset.paginated_serializer_response = Mock(return_value='response')

        response = viewset.rh_candidatos(SimpleNamespace())

        relation_queryset.filter.assert_called_once_with(triagem_automatica_aprovada=True)
        approved_queryset.order_by.assert_called_once_with('-triagem_automatica_pontuacao', 'cpf_candidato')
        viewset.paginated_serializer_response.assert_called_once_with(
            ordered_queryset,
            CandidatoVagaRHReadSerializer,
        )
        self.assertEqual(response, 'response')

    def test_rh_processos_expoe_serializer_com_triagem(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        ordered_queryset = Mock()
        relation_queryset = Mock()
        relation_queryset.order_by.return_value = ordered_queryset
        vaga = SimpleNamespace(
            candidatovaga_set=SimpleNamespace(all=Mock(return_value=relation_queryset)),
        )
        viewset = VagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        viewset.get_object = Mock(return_value=vaga)
        viewset.paginated_serializer_response = Mock(return_value='response')

        response = viewset.rh_processos(SimpleNamespace())

        viewset.paginated_serializer_response.assert_called_once_with(
            ordered_queryset,
            CandidatoVagaRHReadSerializer,
        )
        self.assertEqual(response, 'response')

    def test_rh_triagem_revisao_lista_pendentes_e_reprovados(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        review_queryset = Mock()
        ordered_queryset = Mock()
        relation_queryset = Mock()
        relation_queryset.filter.return_value = review_queryset
        review_queryset.order_by.return_value = ordered_queryset
        vaga = SimpleNamespace(
            candidatovaga_set=SimpleNamespace(all=Mock(return_value=relation_queryset)),
        )
        viewset = VagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        viewset.get_object = Mock(return_value=vaga)
        viewset.paginated_serializer_response = Mock(return_value='response')

        response = viewset.rh_triagem_revisao(SimpleNamespace())

        relation_queryset.filter.assert_called_once_with(
            triagem_automatica_classificacao__in={
                TRIAGEM_CLASSIFICACAO_PENDENTE,
                TRIAGEM_CLASSIFICACAO_REPROVADO_TECNICO,
            }
        )
        review_queryset.order_by.assert_called_once_with('triagem_automatica_pontuacao', 'cpf_candidato')
        viewset.paginated_serializer_response.assert_called_once_with(
            ordered_queryset,
            CandidatoVagaRHReadSerializer,
        )
        self.assertEqual(response, 'response')

    def test_email_serializer_exige_cpfs_para_envio_selecionado(self):
        serializer = CandidatoVagaEmailSerializer(data={
            'tipo_destinatarios': CandidatoVagaEmailSerializer.TIPO_SELECIONADOS,
            'assunto': 'Processo seletivo',
            'mensagem': 'Mensagem segura',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('cpf_candidatos', serializer.errors)

    def test_rh_enviar_email_candidatos_envia_individualmente(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        candidaturas = [
            SimpleNamespace(cpf_candidato=SimpleNamespace(email='ana@example.com')),
            SimpleNamespace(cpf_candidato=SimpleNamespace(email='bia@example.com')),
            SimpleNamespace(cpf_candidato=SimpleNamespace(email='')),
        ]
        viewset = VagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        viewset.get_object = Mock(return_value=Vaga(id_vaga=1))
        viewset.get_candidaturas_para_email = Mock(return_value=candidaturas)

        with patch('apps.candidato_vaga.api.views.send_mail') as send_mail_mock:
            response = viewset.rh_enviar_email_candidatos(
                SimpleNamespace(data={
                    'tipo_destinatarios': CandidatoVagaEmailSerializer.TIPO_APROVADOS,
                    'assunto': 'Processo seletivo',
                    'mensagem': 'Voce segue no processo seletivo.',
                })
            )

        self.assertEqual(send_mail_mock.call_count, 2)
        send_mail_mock.assert_any_call(
            'Processo seletivo',
            'Voce segue no processo seletivo.',
            None,
            ['ana@example.com'],
            fail_silently=False,
        )
        send_mail_mock.assert_any_call(
            'Processo seletivo',
            'Voce segue no processo seletivo.',
            None,
            ['bia@example.com'],
            fail_silently=False,
        )
        self.assertEqual(response.data['total_candidaturas'], 3)
        self.assertEqual(response.data['total_enviados'], 2)
        self.assertEqual(response.data['total_sem_email'], 1)

    def test_get_candidaturas_para_email_filtra_por_tipo_sem_email_externo(self):
        base_queryset = Mock()
        ordered_queryset = Mock()
        ordered_queryset.filter.return_value = ['candidatura']
        base_queryset.select_related.return_value.order_by.return_value = ordered_queryset
        vaga = SimpleNamespace(
            candidatovaga_set=SimpleNamespace(all=Mock(return_value=base_queryset)),
        )
        viewset = VagaViewSet()

        result = viewset.get_candidaturas_para_email(vaga, {
            'tipo_destinatarios': CandidatoVagaEmailSerializer.TIPO_SELECIONADOS,
            'cpf_candidatos': ['12345678901'],
        })

        base_queryset.select_related.assert_called_once_with('cpf_candidato')
        ordered_queryset.filter.assert_called_once_with(cpf_candidato_id__in=['12345678901'])
        self.assertEqual(result, ['candidatura'])


class VagaStatusMigrationTests(SimpleTestCase):
    def test_migration_0003_modela_status_com_default_constraint_e_view(self):
        migration_module = importlib.import_module('apps.candidato_vaga.migrations.0003_add_vaga_status')
        sql = migration_module.Migration.operations[0].database_operations[0].sql

        self.assertIn('ALTER TABLE vaga ADD COLUMN IF NOT EXISTS status varchar(20)', sql)
        self.assertIn("ALTER TABLE vaga ALTER COLUMN status SET DEFAULT 'aberta'", sql)
        self.assertIn('vaga_status_check', sql)
        self.assertIn("CHECK (status IN ('aberta', 'andamento', 'fechada', 'cancelada'))", sql)
        self.assertIn('DROP VIEW IF EXISTS listar_todos_os_candidatos_vaga', sql)
        self.assertIn('v.status AS status_vaga', sql)
        self.assertEqual(
            migration_module.Migration.dependencies,
            [('candidato_vaga', '0002_add_candidato_user')],
        )


class CandidatoCurriculoMigrationTests(SimpleTestCase):
    def test_migration_0004_modela_curriculo_como_filefield_sem_operacao_fisica(self):
        migration_module = importlib.import_module('apps.candidato_vaga.migrations.0004_alter_candidato_curriculo_file')
        operation = migration_module.Migration.operations[0]
        field = operation.state_operations[0].field

        self.assertEqual(operation.database_operations, [])
        self.assertEqual(field.max_length, 255)
        self.assertEqual(field.upload_to, candidato_curriculo_upload_path)
        self.assertEqual(
            migration_module.Migration.dependencies,
            [('candidato_vaga', '0003_add_vaga_status')],
        )


class CandidatoTriagemMigrationTests(SimpleTestCase):
    def test_migration_0005_modela_campos_de_triagem(self):
        migration_module = importlib.import_module('apps.candidato_vaga.migrations.0005_add_candidatura_triagem')
        operation = migration_module.Migration.operations[0]
        sql = operation.database_operations[0].sql
        field_names = [field.name for field in operation.state_operations]

        self.assertIn('triagem_automatica_aprovada boolean', sql)
        self.assertIn('triagem_automatica_motivo text', sql)
        self.assertIn('triagem_automatica_palavras_chave text', sql)
        self.assertIn('cv.triagem_automatica_aprovada', sql)
        self.assertEqual(field_names, [
            'triagem_automatica_aprovada',
            'triagem_automatica_motivo',
            'triagem_automatica_palavras_chave',
        ])
        self.assertEqual(
            migration_module.Migration.dependencies,
            [('candidato_vaga', '0004_alter_candidato_curriculo_file')],
        )

    def test_migration_0006_modela_requisitos_pontuacao_e_classificacao(self):
        migration_module = importlib.import_module(
            'apps.candidato_vaga.migrations.0006_add_vaga_requisitos_triagem_score'
        )
        operation = migration_module.Migration.operations[0]
        sql = operation.database_operations[0].sql
        field_names = [field.name for field in operation.state_operations]

        self.assertIn('ADD COLUMN IF NOT EXISTS requisitos text', sql)
        self.assertIn('triagem_automatica_pontuacao smallint', sql)
        self.assertIn('triagem_automatica_classificacao varchar(40)', sql)
        self.assertIn('v.requisitos AS requisitos_vaga', sql)
        self.assertIn('cv.triagem_automatica_pontuacao', sql)
        self.assertEqual(field_names, [
            'requisitos',
            'triagem_automatica_pontuacao',
            'triagem_automatica_classificacao',
        ])
        self.assertEqual(
            migration_module.Migration.dependencies,
            [('candidato_vaga', '0005_add_candidatura_triagem')],
        )


class CandidatoVagaTestPageTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_tela_teste_renderiza_forms_tabelas_e_botoes(self):
        request = RequestFactory().get('/api/candidato/teste/')

        response = candidato_vaga_test_page(request)
        content = response.content.decode('utf-8')

        self.assertIn('<form id="candidate-form">', content)
        self.assertIn('type="file" accept=".pdf,.doc,.docx"', content)
        self.assertIn('<form id="job-form">', content)
        self.assertIn('id="job_requirements"', content)
        self.assertIn('<form id="application-form">', content)
        self.assertIn('Pontuacao', content)
        self.assertIn('Classificacao', content)
        self.assertIn('Editar', content)
        self.assertIn('Deletar', content)

    @override_settings(DEBUG=False)
    def test_tela_teste_fica_indisponivel_fora_de_debug(self):
        request = RequestFactory().get('/api/candidato/teste/')

        with self.assertRaises(Http404):
            candidato_vaga_test_page(request)


class CandidatoWritePolicyTests(SimpleTestCase):
    def make_viewset(self, action, user):
        viewset = CandidatoViewSet()
        viewset.action = action
        viewset.request = SimpleNamespace(user=user)
        return viewset

    def make_user(self, **overrides):
        user = {
            'is_authenticated': True,
            'is_staff': False,
            'is_superuser': False,
            'pk': None,
            'has_perm': lambda permission: False,
        }
        user.update(overrides)
        return SimpleNamespace(**user)

    def test_candidato_comum_pode_criar_e_editar_proprio_perfil(self):
        for action in ['create', 'update', 'partial_update']:
            with self.subTest(action=action):
                viewset = self.make_viewset(action, self.make_user())

                viewset.assert_candidato_write_policy()
                self.assertIs(viewset.get_serializer_class(), CandidatoWriteSerializer)

    def test_rh_admin_nao_cria_nem_edita_candidato(self):
        user = self.make_user(is_staff=True)

        for action in ['create', 'update', 'partial_update']:
            with self.subTest(action=action):
                viewset = self.make_viewset(action, user)

                with self.assertRaises(PermissionDenied):
                    viewset.assert_candidato_write_policy()

    def test_apenas_rh_admin_pode_deletar_candidato(self):
        self.make_viewset('destroy', self.make_user(is_staff=True)).assert_candidato_write_policy()

        with self.assertRaises(PermissionDenied):
            self.make_viewset('destroy', self.make_user()).assert_candidato_write_policy()


class CandidatoAccessMixinTests(SimpleTestCase):
    def test_candidato_acessa_apenas_proprio_cpf_por_vinculo_formal(self):
        mixin = CandidatoAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                candidato=SimpleNamespace(pk='12345678901'),
            )
        )

        mixin.assert_can_access_candidato('12345678901')

        with self.assertRaises(PermissionDenied):
            mixin.assert_can_access_candidato('00000000000')

    def test_candidato_sem_vinculo_formal_nao_usa_cpf_solto_do_usuario(self):
        mixin = CandidatoAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                cpf_candidato='12345678901',
            )
        )

        with self.assertRaises(PermissionDenied):
            mixin.get_request_candidato_cpf()

    def test_cadastro_do_candidato_vincula_usuario_autenticado(self):
        user = SimpleNamespace(
            is_authenticated=True,
            is_staff=False,
            is_superuser=False,
            pk=10,
            groups=SimpleNamespace(values_list=lambda *args, **kwargs: []),
            has_perm=lambda permission: False,
        )
        serializer = Mock()
        serializer.validated_data = {'cpf_candidato': '12345678901'}
        viewset = CandidatoViewSet()
        viewset.request = SimpleNamespace(user=user)

        viewset.perform_create(serializer)

        serializer.save.assert_called_once_with(user=user)
