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
    CandidatoVagaReadSerializer,
    CandidatoVagaWriteSerializer,
    CandidatoWriteSerializer,
    VagaWriteSerializer,
)
from apps.candidato_vaga.api.test_views import candidato_vaga_test_page
from apps.candidato_vaga.api.views import CandidatoAccessMixin, CandidatoVagaViewSet, CandidatoViewSet, VagaViewSet
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga, candidato_curriculo_upload_path


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


class CandidatoVagaReadSerializerTests(SimpleTestCase):
    def test_read_serializer_expoe_status_da_vaga(self):
        candidatura = CandidatoVaga(
            cpf_candidato=Candidato(cpf_candidato='12345678901'),
            id_vaga=Vaga(id_vaga=1, status=Vaga.STATUS_FECHADA),
            status_processo='candidatado',
        )

        data = CandidatoVagaReadSerializer(candidatura).data

        self.assertEqual(data['status_vaga'], Vaga.STATUS_FECHADA)


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

    def test_rota_registro_publico_de_candidato_existe(self):
        match = resolve('/api/candidato/candidatos/registrar/')

        self.assertEqual(match.url_name, 'candidato-registrar')

    def test_rota_tela_teste_candidato_vaga_existe(self):
        match = resolve('/api/candidato/teste/')

        self.assertEqual(match.url_name, 'candidato-vaga-teste-page')

    def test_lookup_composto_usa_cpf_e_vaga(self):
        viewset = CandidatoVagaViewSet()

        self.assertEqual(
            viewset.parse_composite_lookup('12345678901:7'),
            ('12345678901', '7'),
        )

        with self.assertRaises(NotFound):
            viewset.parse_composite_lookup('12345678901')

    def test_indicadores_de_vagas_usam_queryset_filtrado(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)
        viewset = VagaViewSet()
        viewset.request = SimpleNamespace(user=user)
        vagas_queryset = Mock()
        vagas_queryset.count.return_value = 2
        vagas_queryset.values.return_value.annotate.return_value.order_by.return_value = [
            {'status': Vaga.STATUS_ABERTA, 'total': 2},
        ]
        viewset.get_queryset = Mock(return_value='base-queryset')
        viewset.filter_queryset = Mock(return_value=vagas_queryset)

        with patch('apps.candidato_vaga.api.views.Candidato.objects.count', return_value=3):
            with patch('apps.candidato_vaga.api.views.CandidatoVaga.objects.count', return_value=4):
                with patch('apps.candidato_vaga.api.views.CandidatoVaga.objects.values') as values_mock:
                    values_mock.return_value.annotate.return_value.order_by.return_value = [
                        {'status_processo': 'candidatado', 'total': 4},
                    ]

                    response = viewset.rh_indicadores(SimpleNamespace())

        viewset.filter_queryset.assert_called_once_with('base-queryset')
        self.assertEqual(response.data['total_vagas'], 2)
        self.assertEqual(response.data['vagas_por_status'], {Vaga.STATUS_ABERTA: 2})


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


class CandidatoVagaTestPageTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_tela_teste_renderiza_forms_tabelas_e_botoes(self):
        request = RequestFactory().get('/api/candidato/teste/')

        response = candidato_vaga_test_page(request)
        content = response.content.decode('utf-8')

        self.assertIn('<form id="candidate-form">', content)
        self.assertIn('type="file" accept=".pdf,.doc,.docx"', content)
        self.assertIn('<form id="job-form">', content)
        self.assertIn('<form id="application-form">', content)
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
