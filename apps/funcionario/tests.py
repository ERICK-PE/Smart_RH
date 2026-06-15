import importlib
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.api_mixins import FuncionarioComumAccessMixin, RHAdminAccessMixin
from apps.funcionario.api.filters import FuncionarioFilter
from apps.funcionario.api.test_views import funcionario_test_page
from apps.funcionario.api.serializers import FuncionarioReadSerializer, FuncionarioWriteSerializer
from apps.funcionario.api.views import FuncionarioViewSet
from apps.funcionario.models import Funcionario


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
        }

        for path, action in expected_routes.items():
            with self.subTest(path=path):
                match = resolve(path)

                self.assertEqual(match.func.actions['post'], action)

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
            patch('apps.funcionario.api.views.PlanoCarreira.objects.count', return_value=4),
        ):
            response = viewset.rh_indicadores(request)

        viewset.filter_queryset.assert_called_once_with('base-queryset')
        self.assertEqual(response.data['total_funcionarios'], 2)
        self.assertEqual(response.data['total_contratos'], 3)
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
