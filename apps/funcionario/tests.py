from types import SimpleNamespace

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.api_mixins import FuncionarioComumAccessMixin, RHAdminAccessMixin
from apps.funcionario.api.test_views import funcionario_test_page
from apps.funcionario.api.serializers import FuncionarioReadSerializer, FuncionarioWriteSerializer
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
