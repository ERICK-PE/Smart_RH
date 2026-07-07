import importlib
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser

from apps.api_mixins import FuncionarioComumAccessMixin, RHAdminAccessMixin
from apps.funcionario.api.filters import FuncionarioFilter
from apps.funcionario.api.test_views import agente_test_page, funcionario_test_page
from apps.funcionario.api.serializers import (
    ContratoReadSerializer,
    ContratoWriteSerializer,
    FolhaPagamentoReadSerializer,
    FolhaPagamentoWriteSerializer,
    FuncionarioAgenteDocumentoWriteSerializer,
    FuncionarioReadSerializer,
    FuncionarioWriteSerializer,
)
from apps.funcionario.api.views import (
    ContratoViewSet,
    FolhaPagamentoViewSet,
    FuncionarioAgenteDocumentoViewSet,
    FuncionarioViewSet,
)
from apps.funcionario.models import (
    Contrato,
    FolhaPagamento,
    Funcionario,
    FuncionarioAgenteDocumento,
    PlanoCarreira,
    contrato_upload_path,
    folha_pagamento_upload_path,
    funcionario_agente_documento_upload_path,
)
from apps.funcionario.services.agente_documentos import (
    answer_question_with_openai,
    delete_important_document_file,
    load_important_document_sources,
    save_important_document_upload,
    validate_document_file,
)


class RHAdminAccessMixinTests(SimpleTestCase):
    def test_usuario_sem_perfil_rh_admin_nao_tem_acesso(self):
        mixin = RHAdminAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                pk=None,
                has_perm=lambda permission: False,
            )
        )

        self.assertFalse(mixin.user_has_rh_admin_access())

        with self.assertRaises(PermissionDenied):
            mixin.assert_rh_admin_access()

    def test_staff_tem_acesso_rh_admin(self):
        mixin = RHAdminAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=True,
                is_superuser=False,
                pk=None,
            )
        )

        self.assertTrue(mixin.user_has_rh_admin_access())


class FuncionarioComumAccessMixinTests(SimpleTestCase):
    def test_usuario_sem_vinculo_formal_nao_usa_id_como_fallback(self):
        mixin = FuncionarioComumAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                id=10,
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                pk=None,
                has_perm=lambda permission: False,
            )
        )

        with self.assertRaises(PermissionDenied):
            mixin.get_request_funcionario_id()

    def test_lideranca_edita_apenas_avaliacao_propria_sem_manage_lideranca(self):
        mixin = FuncionarioComumAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                funcionario_id=1,
                pk=None,
                has_perm=lambda permission: False,
            )
        )

        mixin.assert_can_edit_lideranca_avaliacao(SimpleNamespace(fk_id_avaliador_id=1))

        with self.assertRaises(PermissionDenied):
            mixin.assert_can_edit_lideranca_avaliacao(SimpleNamespace(fk_id_avaliador_id=2))

    def test_manage_lideranca_permite_editar_avaliacao_de_outro_autor(self):
        mixin = FuncionarioComumAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                funcionario_id=1,
                pk=None,
                has_perm=lambda permission: permission == 'funcionario.manage_lideranca',
            )
        )

        mixin.assert_can_edit_lideranca_avaliacao(SimpleNamespace(fk_id_avaliador_id=2))

    def test_lideranca_edita_apenas_plano_proprio_sem_manage_lideranca(self):
        mixin = FuncionarioComumAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                funcionario_id=1,
                pk=None,
                has_perm=lambda permission: False,
            )
        )

        mixin.assert_can_edit_lideranca_plano(SimpleNamespace(fk_id_criador_id=1))

        with self.assertRaises(PermissionDenied):
            mixin.assert_can_edit_lideranca_plano(SimpleNamespace(fk_id_criador_id=2))

    def test_manage_lideranca_permite_editar_plano_de_outro_autor(self):
        mixin = FuncionarioComumAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                funcionario_id=1,
                pk=None,
                has_perm=lambda permission: permission == 'funcionario.manage_lideranca',
            )
        )

        mixin.assert_can_edit_lideranca_plano(SimpleNamespace(fk_id_criador_id=2))


class FuncionarioReadSerializerTests(SimpleTestCase):
    def test_dados_sensiveis_sao_mascarados_sem_contexto_privilegiado(self):
        funcionario = Funcionario(
            id_funcionario=1,
            nome='Maria',
            cpf='123.456.789-00',
            email='maria@example.com',
            telefone='11999999999',
            data_admissao='2024-01-01',
        )

        data = FuncionarioReadSerializer(funcionario).data

        self.assertEqual(data['cpf'], '***.***.***-**')
        self.assertEqual(data['email'], 'm***@example.com')
        self.assertEqual(data['telefone'], '***********')

    def test_serializer_expoe_status(self):
        funcionario = Funcionario(
            id_funcionario=1,
            nome='Maria',
            cpf='123.456.789-00',
            email='maria@example.com',
            telefone='11999999999',
            data_admissao='2024-01-01',
            status=Funcionario.STATUS_ATIVO,
        )

        data = FuncionarioReadSerializer(funcionario).data

        self.assertEqual(data['status'], Funcionario.STATUS_ATIVO)


class FuncionarioWriteSerializerTests(SimpleTestCase):
    def test_status_aceita_apenas_valores_validos(self):
        serializer = FuncionarioWriteSerializer()

        self.assertEqual(serializer.validate_status('Ativo'), Funcionario.STATUS_ATIVO)

        with self.assertRaises(serializers.ValidationError):
            serializer.validate_status('bloqueado')


class FuncionarioStatusAPITests(SimpleTestCase):
    def make_staff_request(self, path):
        request = RequestFactory().post(path)
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_staff=True,
            is_superuser=False,
            pk=1,
        )
        return request

    def test_rotas_rh_inativar_e_reativar_resolvem_para_actions(self):
        expected_routes = {
            '/api/funcionario/funcionarios/1/rh/inativar/': 'rh_inativar',
            '/api/funcionario/funcionarios/1/rh/reativar/': 'rh_reativar',
            '/api/funcionario/funcionarios/1/lideranca/avaliacoes-desempenho/': 'lideranca_avaliacoes_desempenho',
            '/api/funcionario/funcionarios/1/lideranca/planos-carreira/2/editar/': 'lideranca_editar_plano_carreira',
        }

        for path, action in expected_routes.items():
            with self.subTest(path=path):
                match = resolve(path)

                method = 'patch' if 'editar' in path else 'get' if 'avaliacoes-desempenho' in path else 'post'
                self.assertEqual(match.func.actions[method], action)

    def test_rh_inativar_altera_status_sem_remover_registro(self):
        funcionario = Funcionario(
            id_funcionario=1,
            nome='Maria',
            cpf='123.456.789-00',
            data_admissao='2024-01-01',
            status=Funcionario.STATUS_ATIVO,
        )
        funcionario.save = Mock()
        viewset = FuncionarioViewSet()
        viewset.request = self.make_staff_request('/api/funcionario/funcionarios/1/rh/inativar/')
        viewset.kwargs = {'pk': '1'}
        viewset.get_object = Mock(return_value=funcionario)
        viewset.get_serializer = Mock(return_value=SimpleNamespace(data={'status': Funcionario.STATUS_INATIVO}))

        response = viewset.rh_inativar(viewset.request, pk='1')

        self.assertEqual(funcionario.status, Funcionario.STATUS_INATIVO)
        funcionario.save.assert_called_once_with(update_fields=['status'])
        self.assertEqual(response.data['status'], Funcionario.STATUS_INATIVO)

    def test_rh_reativar_altera_status_sem_remover_registro(self):
        funcionario = Funcionario(
            id_funcionario=1,
            nome='Maria',
            cpf='123.456.789-00',
            data_admissao='2024-01-01',
            status=Funcionario.STATUS_INATIVO,
        )
        funcionario.save = Mock()
        viewset = FuncionarioViewSet()
        viewset.request = self.make_staff_request('/api/funcionario/funcionarios/1/rh/reativar/')
        viewset.kwargs = {'pk': '1'}
        viewset.get_object = Mock(return_value=funcionario)
        viewset.get_serializer = Mock(return_value=SimpleNamespace(data={'status': Funcionario.STATUS_ATIVO}))

        response = viewset.rh_reativar(viewset.request, pk='1')

        self.assertEqual(funcionario.status, Funcionario.STATUS_ATIVO)
        funcionario.save.assert_called_once_with(update_fields=['status'])
        self.assertEqual(response.data['status'], Funcionario.STATUS_ATIVO)

    def test_rh_inativar_bloqueia_usuario_sem_perfil_rh(self):
        viewset = FuncionarioViewSet()
        request = RequestFactory().post('/api/funcionario/funcionarios/1/rh/inativar/')
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_staff=False,
            is_superuser=False,
            pk=None,
            has_perm=lambda permission: False,
        )
        viewset.request = request

        with self.assertRaises(PermissionDenied):
            viewset.rh_inativar(request, pk='1')

    def test_indicadores_rh_usam_queryset_filtrado(self):
        request = RequestFactory().get('/api/funcionario/funcionarios/rh/indicadores/?status=ativo')
        request.user = SimpleNamespace(
            is_authenticated=True,
            is_staff=True,
            is_superuser=False,
            pk=1,
        )
        filtered_queryset = Mock()
        filtered_queryset.count.return_value = 2
        filtered_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {'status': Funcionario.STATUS_ATIVO, 'total': 2},
        ]
        viewset = FuncionarioViewSet()
        viewset.request = request
        viewset.get_queryset = Mock(return_value='base-queryset')
        viewset.filter_queryset = Mock(return_value=filtered_queryset)

        with (
            patch('apps.funcionario.api.views.Contrato.objects.count', return_value=3),
            patch('apps.funcionario.api.views.FolhaPagamento.objects.count', return_value=5),
            patch('apps.funcionario.api.views.PlanoCarreira.objects.count', return_value=4),
        ):
            response = viewset.rh_indicadores(request)

        viewset.filter_queryset.assert_called_once_with('base-queryset')
        self.assertEqual(response.data['total_funcionarios'], 2)
        self.assertEqual(response.data['total_contratos'], 3)
        self.assertEqual(response.data['total_folhas_pagamento'], 5)
        self.assertEqual(response.data['total_planos_carreira'], 4)
        self.assertEqual(response.data['funcionarios_por_status'], {Funcionario.STATUS_ATIVO: 2})


class FuncionarioStatusFilterTests(SimpleTestCase):
    def test_filtro_status_usa_comparacao_case_insensitive(self):
        status_filter = FuncionarioFilter.base_filters['status']

        self.assertEqual(status_filter.field_name, 'status')
        self.assertEqual(status_filter.lookup_expr, 'iexact')


class FuncionarioStatusMigrationTests(SimpleTestCase):
    def test_migration_0003_modela_status_com_default_e_constraint(self):
        migration_module = importlib.import_module('apps.funcionario.migrations.0003_add_funcionario_status')
        sql = migration_module.Migration.operations[0].sql

        self.assertIn("ADD COLUMN IF NOT EXISTS status varchar(20) NOT NULL DEFAULT 'ativo'", sql)
        self.assertIn('funcionario_status_check', sql)
        self.assertIn("CHECK (status IN ('ativo', 'inativo'))", sql)
        self.assertEqual(
            migration_module.Migration.dependencies,
            [('funcionario', '0002_add_funcionario_user')],
        )


class ContratoFolhaPagamentoUploadTests(SimpleTestCase):
    def make_file(self, filename='documento.pdf', content_type='application/pdf'):
        return SimpleUploadedFile(filename, b'conteudo', content_type=content_type)

    def make_staff_request(self, data=None):
        return SimpleNamespace(
            data=data or {},
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=True,
                is_superuser=False,
                pk=1,
            ),
        )

    def test_upload_paths_usam_pastas_proprias_sem_cpf(self):
        self.assertEqual(
            contrato_upload_path(SimpleNamespace(), '../../Contrato Final.PDF'),
            'contratos/Contrato_Final.pdf',
        )
        self.assertEqual(
            folha_pagamento_upload_path(SimpleNamespace(), '../../Folha Junho.DOCX'),
            'folhas_pagamento/Folha_Junho.docx',
        )

    def test_serializers_aceitam_pdf_doc_docx_e_rejeitam_txt(self):
        valid_files = [
            ('contrato.pdf', 'application/pdf'),
            ('contrato.doc', 'application/msword'),
            (
                'contrato.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ),
        ]

        for filename, content_type in valid_files:
            with self.subTest(filename=filename):
                ContratoWriteSerializer().fields['arquivo'].run_validation(self.make_file(filename, content_type))
                FolhaPagamentoWriteSerializer().fields['arquivo'].run_validation(self.make_file(filename, content_type))

        with self.assertRaises(serializers.ValidationError):
            ContratoWriteSerializer().fields['arquivo'].run_validation(self.make_file('contrato.txt', 'text/plain'))

        with self.assertRaises(serializers.ValidationError):
            FolhaPagamentoWriteSerializer().fields['arquivo'].run_validation(self.make_file('folha.txt', 'text/plain'))

    def test_read_serializers_retorna_caminho_para_contexto_rh(self):
        request = self.make_staff_request()
        view = FuncionarioViewSet()
        view.request = request
        contrato = Contrato(
            id_contrato=1,
            arquivo='contratos/contrato.pdf',
            fk_id_funcionario=Funcionario(id_funcionario=1),
        )
        folha = FolhaPagamento(
            id_folha=1,
            arquivo='folhas_pagamento/folha.pdf',
            fk_id_funcionario=Funcionario(id_funcionario=1),
        )
        context = {'request': request, 'view': view}

        self.assertEqual(ContratoReadSerializer(contrato, context=context).data['arquivo'], 'contratos/contrato.pdf')
        self.assertEqual(
            FolhaPagamentoReadSerializer(folha, context=context).data['arquivo'],
            'folhas_pagamento/folha.pdf',
        )

    def test_rotas_de_upload_e_consulta_resolvem(self):
        expected_routes = {
            '/api/funcionario/folhas-pagamento/': ('get', 'list'),
            '/api/funcionario/folhas-pagamento/1/': ('get', 'retrieve'),
            '/api/funcionario/funcionarios/1/rh/folha-pagamento/': ('post', 'rh_folha_pagamento'),
            '/api/funcionario/funcionarios/1/folha-pagamento/': ('get', 'folha_pagamento'),
            '/api/funcionario/contratos/1/rh/arquivo/': ('post', 'rh_arquivo'),
        }

        for path, (method, action) in expected_routes.items():
            with self.subTest(path=path):
                match = resolve(path)

                self.assertEqual(match.func.actions[method], action)

    def test_upload_viewsets_aceitam_multipart(self):
        self.assertIn(MultiPartParser, FuncionarioViewSet.parser_classes)
        self.assertIn(MultiPartParser, ContratoViewSet.parser_classes)
        self.assertIn(MultiPartParser, FolhaPagamentoViewSet.parser_classes)

    def test_rh_folha_pagamento_define_funcionario_e_cria_registro(self):
        funcionario = Funcionario(id_funcionario=7, nome='Maria', data_admissao='2024-01-01')
        folha = FolhaPagamento(id_folha=1, fk_id_funcionario=funcionario, arquivo='folhas_pagamento/folha.pdf')
        request = self.make_staff_request({
            'competencia': '2026-06',
            'arquivo': self.make_file('folha.pdf', 'application/pdf'),
        })
        viewset = FuncionarioViewSet()
        viewset.request = request
        viewset.get_object = Mock(return_value=funcionario)
        viewset.get_serializer_context = Mock(return_value={'request': request, 'view': viewset})

        serializer = Mock()
        serializer.is_valid = Mock()
        serializer.save.return_value = folha

        with (
            patch('apps.funcionario.api.views.FolhaPagamentoWriteSerializer', return_value=serializer) as write_mock,
            patch(
                'apps.funcionario.api.views.FolhaPagamentoReadSerializer',
                return_value=SimpleNamespace(data={'id_folha': 1, 'arquivo': 'folhas_pagamento/folha.pdf'}),
            ),
        ):
            response = viewset.rh_folha_pagamento(request, pk='7')

        payload = write_mock.call_args.kwargs['data']
        self.assertEqual(payload['fk_id_funcionario'], 7)
        serializer.is_valid.assert_called_once_with(raise_exception=True)
        serializer.save.assert_called_once_with()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['arquivo'], 'folhas_pagamento/folha.pdf')

    def test_rh_arquivo_contrato_exige_arquivo(self):
        request = self.make_staff_request({})
        viewset = ContratoViewSet()
        viewset.request = request
        viewset.get_object = Mock(return_value=Contrato(id_contrato=1))

        response = viewset.rh_arquivo(request, pk='1')

        self.assertEqual(response.status_code, 400)
        self.assertIn('arquivo', response.data)


class ContratoFolhaPagamentoMigrationTests(SimpleTestCase):
    def test_migration_0005_adiciona_arquivo_contrato_e_cria_folha(self):
        migration_module = importlib.import_module('apps.funcionario.migrations.0005_contrato_arquivo_folha_pagamento')
        operation = migration_module.Migration.operations[0]
        sql = operation.database_operations[0].sql
        state_operation_names = [state_operation.__class__.__name__ for state_operation in operation.state_operations]

        self.assertIn('ADD COLUMN IF NOT EXISTS arquivo varchar(255)', sql)
        self.assertIn('CREATE TABLE IF NOT EXISTS folha_pagamento', sql)
        self.assertIn('fk_id_funcionario integer NOT NULL', sql)
        self.assertEqual(
            migration_module.Migration.dependencies,
            [('funcionario', '0004_funcionarioagentedocumento')],
        )
        self.assertEqual(state_operation_names, ['AddField', 'CreateModel'])


class PlanoCarreiraCriadorMigrationTests(SimpleTestCase):
    def test_migration_0006_adiciona_criador_do_plano(self):
        migration_module = importlib.import_module('apps.funcionario.migrations.0006_plano_carreira_criador')
        operation = migration_module.Migration.operations[0]
        sql = operation.database_operations[0].sql
        state_operation = operation.state_operations[0]

        self.assertIn('ADD COLUMN IF NOT EXISTS fk_id_criador integer NULL', sql)
        self.assertIn('REFERENCES funcionario(id_funcionario)', sql)
        self.assertEqual(state_operation.name, 'fk_id_criador')
        self.assertEqual(state_operation.field.db_column, 'fk_id_criador')


class FuncionarioAgenteDocumentoTests(SimpleTestCase):
    def make_docx_file(self, text='Ferias devem ser solicitadas com 30 dias de antecedencia.'):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr(
                'word/document.xml',
                (
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    f'<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>'
                    '</w:document>'
                ),
            )
        return SimpleUploadedFile(
            'politica.docx',
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )

    def test_upload_path_sanitiza_nome_do_documento(self):
        path = funcionario_agente_documento_upload_path(
            SimpleNamespace(),
            '../../Politica RH Interna.DOCX',
        )

        self.assertEqual(path, 'imp_doc/Politica RH Interna.DOCX')

    def test_save_upload_preserva_nome_original_em_imp_doc(self):
        with TemporaryDirectory() as tmpdir:
            with override_settings(BASE_DIR=Path(tmpdir)):
                upload = self.make_docx_file()
                upload.name = 'Politica RH Interna.DOCX'

                relative_path = save_important_document_upload(upload)

                self.assertEqual(relative_path, 'imp_doc/Politica RH Interna.DOCX')
                self.assertTrue((Path(tmpdir) / relative_path).exists())

    def test_serializer_rejeita_extensao_invalida(self):
        serializer = FuncionarioAgenteDocumentoWriteSerializer(data={
            'titulo': 'Politica RH',
            'arquivo': SimpleUploadedFile('politica.txt', b'conteudo', content_type='text/plain'),
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('arquivo', serializer.errors)

    def test_validacao_aceita_pdf_doc_e_docx(self):
        arquivos = [
            ('politica.pdf', 'application/pdf'),
            ('politica.doc', 'application/msword'),
            (
                'politica.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ),
        ]

        for filename, content_type in arquivos:
            with self.subTest(filename=filename):
                validate_document_file(SimpleUploadedFile(filename, b'conteudo', content_type=content_type))

    def test_serializer_extrai_texto_de_docx(self):
        serializer = FuncionarioAgenteDocumentoWriteSerializer(data={
            'titulo': 'Politica RH',
            'arquivo': self.make_docx_file(),
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn('Ferias devem ser solicitadas', serializer.validated_data['conteudo_extraido'])

    def test_serializer_extrai_texto_de_doc_legado_best_effort(self):
        serializer = FuncionarioAgenteDocumentoWriteSerializer(data={
            'titulo': 'Politica RH',
            'arquivo': SimpleUploadedFile(
                'politica.doc',
                b'\x00\x01Ferias coletivas seguem calendario do RH.\x00\x02',
                content_type='application/msword',
            ),
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn('Ferias coletivas', serializer.validated_data['conteudo_extraido'])

    def test_serializer_rejeita_documento_maior_que_limite(self):
        serializer = FuncionarioAgenteDocumentoWriteSerializer(data={
            'titulo': 'Politica RH',
            'arquivo': SimpleUploadedFile(
                'politica.pdf',
                b'0' * ((10 * 1024 * 1024) + 1),
                content_type='application/pdf',
            ),
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('arquivo', serializer.errors)

    def test_load_important_document_sources_usa_somente_cadastro_ativo(self):
        with TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir) / 'imp_doc'
            docs_dir.mkdir()
            upload = self.make_docx_file()
            (docs_dir / 'Politica RH Interna.DOCX').write_bytes(upload.read())

            with override_settings(BASE_DIR=Path(tmpdir)):
                documentos = load_important_document_sources([
                    FuncionarioAgenteDocumento(
                        id_documento=1,
                        titulo='Politica ativa',
                        conteudo_extraido='Ferias devem ser solicitadas com 30 dias de antecedencia.',
                        arquivo='imp_doc/politica-ativa.docx',
                        ativo=True,
                    ),
                    FuncionarioAgenteDocumento(
                        id_documento=2,
                        titulo='Politica inativa',
                        conteudo_extraido='Conteudo inativo nao deve ser usado.',
                        arquivo='imp_doc/politica-inativa.docx',
                        ativo=False,
                    ),
                ])

        self.assertEqual(len(documentos), 1)
        self.assertEqual(documentos[0].id_documento, 1)
        self.assertEqual(documentos[0].titulo, 'Politica ativa')
        self.assertIn('Ferias devem ser solicitadas', documentos[0].conteudo_extraido)
        self.assertNotIn('Politica RH Interna.DOCX', [documento.titulo for documento in documentos])

    def test_update_documento_remove_arquivo_antigo_quando_upload_troca(self):
        with TemporaryDirectory() as tmpdir:
            with override_settings(BASE_DIR=Path(tmpdir)):
                old_path = Path(tmpdir) / 'imp_doc' / 'antigo.docx'
                old_path.parent.mkdir()
                old_path.write_bytes(b'antigo')
                documento = FuncionarioAgenteDocumento(
                    id_documento=1,
                    titulo='Politica antiga',
                    conteudo_extraido='Texto antigo',
                    arquivo='imp_doc/antigo.docx',
                    ativo=True,
                )
                documento.save = Mock()
                upload = self.make_docx_file()
                upload.name = 'novo.docx'
                serializer = FuncionarioAgenteDocumentoWriteSerializer(
                    documento,
                    data={'titulo': 'Politica nova', 'arquivo': upload},
                    partial=True,
                )

                self.assertTrue(serializer.is_valid(), serializer.errors)
                serializer.save()

                self.assertFalse(old_path.exists())
                self.assertTrue((Path(tmpdir) / 'imp_doc' / 'novo.docx').exists())

    def test_delete_important_document_file_remove_apenas_arquivo_em_imp_doc(self):
        with TemporaryDirectory() as tmpdir:
            with override_settings(BASE_DIR=Path(tmpdir)):
                docs_dir = Path(tmpdir) / 'imp_doc'
                docs_dir.mkdir()
                target = docs_dir / 'politica.docx'
                target.write_bytes(b'conteudo')

                delete_important_document_file('imp_doc/politica.docx')
                delete_important_document_file('../fora.docx')

        self.assertFalse(target.exists())

    def test_agente_responde_usando_openai_com_contexto_dos_documentos(self):
        documento = FuncionarioAgenteDocumento(
            id_documento=1,
            titulo='Politica de ferias',
            conteudo_extraido='Ferias devem ser solicitadas com 30 dias de antecedencia.',
            arquivo='imp_doc/politica.docx',
        )
        mock_client = Mock()
        mock_client.responses.create.return_value = SimpleNamespace(
            output_text='Ferias devem ser solicitadas com 30 dias de antecedencia.'
        )

        with (
            patch.dict(os.environ, {'OPEN_API_KEY': 'test-key'}),
            patch('apps.funcionario.services.agente_documentos.OpenAI', return_value=mock_client) as openai_mock,
        ):
            resposta = answer_question_with_openai('Como solicitar ferias?', [documento])

        openai_mock.assert_called_once_with(api_key='test-key')
        request_payload = mock_client.responses.create.call_args.kwargs
        self.assertIn('Ferias devem ser solicitadas', request_payload['input'][1]['content'])
        self.assertIn('Ferias devem ser solicitadas', resposta['resposta'])
        self.assertEqual(resposta['fontes'][0]['titulo'], 'Politica de ferias')

    def test_agente_falha_sem_open_api_key(self):
        documento = FuncionarioAgenteDocumento(
            id_documento=1,
            titulo='Politica de ferias',
            conteudo_extraido='Ferias devem ser solicitadas com 30 dias de antecedencia.',
        )

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesMessage(ValueError, 'OPEN_API_KEY nao configurada.'):
                answer_question_with_openai('Como solicitar ferias?', [documento])


class FuncionarioAgenteDocumentoAPITests(SimpleTestCase):
    def test_rota_perguntar_agente_funcionario_existe(self):
        match = resolve('/api/funcionario/agente/perguntar/')

        self.assertEqual(match.url_name, 'funcionario-agente-perguntar')
        self.assertEqual(match.func.actions['post'], 'perguntar')

    def test_perguntar_bloqueia_usuario_sem_vinculo_funcionario(self):
        viewset = FuncionarioAgenteDocumentoViewSet()
        request = SimpleNamespace(
            data={'pergunta': 'Como solicitar ferias?'},
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                pk=None,
                has_perm=lambda permission: False,
            ),
        )
        viewset.request = request

        with self.assertRaises(PermissionDenied):
            viewset.perguntar(request)

    def test_perguntar_retorna_resposta_com_fontes(self):
        documentos = [
            SimpleNamespace(
                id_documento=1,
                titulo='Politica de ferias',
                conteudo_extraido='Ferias devem ser solicitadas com 30 dias de antecedencia.',
                arquivo='imp_doc/politica.docx',
            )
        ]
        viewset = FuncionarioAgenteDocumentoViewSet()
        request = SimpleNamespace(
            data={'pergunta': 'Como solicitar ferias?'},
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                funcionario_id=1,
                pk=None,
                has_perm=lambda permission: False,
            ),
        )
        viewset.request = request

        with (
            patch('apps.funcionario.api.views.load_important_document_sources', return_value=documentos),
            patch('apps.funcionario.api.views.answer_question_with_openai', return_value={
                'resposta': 'Ferias devem ser solicitadas com 30 dias de antecedencia.',
                'fontes': [{'titulo': 'Politica de ferias', 'arquivo': 'imp_doc/politica.docx'}],
            }) as answer_mock,
        ):
            response = viewset.perguntar(request)

        answer_mock.assert_called_once_with('Como solicitar ferias?', documentos)
        self.assertIn('Ferias devem ser solicitadas', response.data['resposta'])
        self.assertEqual(response.data['fontes'][0]['titulo'], 'Politica de ferias')

    def test_perguntar_permite_rh_admin_sem_vinculo_funcionario(self):
        viewset = FuncionarioAgenteDocumentoViewSet()
        request = SimpleNamespace(
            data={'pergunta': 'Como solicitar ferias?'},
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=True,
                is_superuser=False,
                pk=1,
            ),
        )
        viewset.request = request

        with (
            patch('apps.funcionario.api.views.load_important_document_sources', return_value=[
                SimpleNamespace(titulo='Politica', conteudo_extraido='Texto', arquivo='imp_doc/politica.docx')
            ]),
            patch('apps.funcionario.api.views.answer_question_with_openai', return_value={
                'resposta': 'Resposta RH',
                'fontes': [],
            }),
        ):
            response = viewset.perguntar(request)

        self.assertEqual(response.data['resposta'], 'Resposta RH')

    def test_perform_destroy_remove_arquivo_fisico_do_documento(self):
        with TemporaryDirectory() as tmpdir:
            with override_settings(BASE_DIR=Path(tmpdir)):
                docs_dir = Path(tmpdir) / 'imp_doc'
                docs_dir.mkdir()
                target = docs_dir / 'politica.docx'
                target.write_bytes(b'conteudo')
                documento = FuncionarioAgenteDocumento(
                    id_documento=1,
                    titulo='Politica',
                    conteudo_extraido='Texto',
                    arquivo='imp_doc/politica.docx',
                )
                documento.delete = Mock()
                viewset = FuncionarioAgenteDocumentoViewSet()

                viewset.perform_destroy(documento)

        documento.delete.assert_called_once()
        self.assertFalse(target.exists())


class FuncionarioAgenteDocumentoMigrationTests(SimpleTestCase):
    def test_migration_0004_cria_tabela_de_documentos_do_agente(self):
        migration_module = importlib.import_module('apps.funcionario.migrations.0004_funcionarioagentedocumento')
        operation = migration_module.Migration.operations[0]
        field_by_name = dict(operation.fields)

        self.assertEqual(operation.name, 'FuncionarioAgenteDocumento')
        self.assertEqual(operation.options['db_table'], 'agente_documento')
        self.assertEqual(field_by_name['criado_por'].db_column, 'id_usuario')
        self.assertEqual(
            migration_module.Migration.dependencies[0],
            ('funcionario', '0003_add_funcionario_status'),
        )


class FuncionarioTestPageTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_tela_teste_renderiza_form_tabela_e_botoes(self):
        request = RequestFactory().get('/api/funcionario/teste/')

        response = funcionario_test_page(request)
        content = response.content.decode('utf-8')

        self.assertContains(response, '<form id="funcionario-form"', html=False)
        self.assertIn('<tbody id="funcionarios-body"></tbody>', content)
        self.assertIn('Editar', content)
        self.assertIn('Deletar', content)

    @override_settings(DEBUG=False)
    def test_tela_teste_fica_indisponivel_fora_de_debug(self):
        request = RequestFactory().get('/api/funcionario/teste/')

        with self.assertRaises(Http404):
            funcionario_test_page(request)


class AgenteTestPageTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_rota_tela_teste_agente_existe(self):
        match = resolve('/api/funcionario/teste/agente/')

        self.assertEqual(match.url_name, 'funcionario-agente-teste-page')

    @override_settings(DEBUG=True)
    def test_rotas_api_teste_agente_existem(self):
        expected_routes = {
            '/api/funcionario/teste/api/agente/upload/': 'funcionario-agente-teste-upload',
            '/api/funcionario/teste/api/agente/perguntar/': 'funcionario-agente-teste-perguntar',
        }

        for path, url_name in expected_routes.items():
            with self.subTest(path=path):
                self.assertEqual(resolve(path).url_name, url_name)

    @override_settings(DEBUG=True)
    def test_tela_teste_agente_renderiza_forms_e_outputs(self):
        request = RequestFactory().get('/api/funcionario/teste/agente/')

        response = agente_test_page(request)
        content = response.content.decode('utf-8')

        self.assertContains(response, '<form id="pergunta-form"', html=False)
        self.assertContains(response, '<form id="upload-form"', html=False)
        self.assertIn('id="resposta"', content)
        self.assertIn('id="upload-output"', content)
        self.assertIn('accept=".pdf,.doc,.docx"', content)

    @override_settings(DEBUG=False)
    def test_tela_teste_agente_fica_indisponivel_fora_de_debug(self):
        request = RequestFactory().get('/api/funcionario/teste/agente/')

        with self.assertRaises(Http404):
            agente_test_page(request)
