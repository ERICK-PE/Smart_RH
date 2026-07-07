from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AvaliacaoDesempenhoReadSerializer,
)
from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho
from apps.candidato_vaga.api.serializers import CandidatoReadSerializer, CandidatoVagaReadSerializer
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga
from apps.funcionario.api.serializers import (
    ContratoReadSerializer,
    FolhaPagamentoReadSerializer,
    FuncionarioReadSerializer,
)
from apps.funcionario.models import Contrato, FolhaPagamento, Funcionario
from apps.setor.models import Cargo, Setor


class SensitiveSerializerTests(SimpleTestCase):
    forbidden_auth_keys = {
        'password',
        'is_superuser',
        'is_staff',
        'user_permissions',
        'last_login',
    }
    forbidden_relation_sensitive_keys = {
        'cpf',
        'email',
        'telefone',
        'user',
    }

    def assert_payload_omits_keys(self, payload, forbidden_keys):
        if isinstance(payload, dict):
            for key, value in payload.items():
                self.assertNotIn(key, forbidden_keys)
                self.assert_payload_omits_keys(value, forbidden_keys)
        elif isinstance(payload, list):
            for item in payload:
                self.assert_payload_omits_keys(item, forbidden_keys)

    def make_user(self, username='usuario'):
        UserModel = get_user_model()
        return UserModel(
            id=99,
            username=username,
            email=f'{username}@example.com',
            password='pbkdf2_sha256$hash-interno',
            is_staff=True,
            is_superuser=True,
        )

    def make_funcionario(self, id_funcionario=1, nome='Maria'):
        return Funcionario(
            id_funcionario=id_funcionario,
            user=self.make_user(f'user{id_funcionario}'),
            nome=nome,
            cpf='12345678901',
            email=f'{nome.lower()}@example.com',
            telefone='11999999999',
            status=Funcionario.STATUS_ATIVO,
            fk_id_setor=Setor(id_setor=1, nome='RH'),
            fk_id_cargo=Cargo(id_cargo=1, nome='Analista'),
        )

    def test_candidato_read_serializer_mascara_dados_sem_contexto_privilegiado(self):
        candidato = Candidato(
            cpf_candidato='12345678901',
            user=self.make_user('candidato'),
            nome='Joao',
            email='joao@example.com',
            telefone='11999999999',
            curriculo='Curriculo confidencial',
        )

        data = CandidatoReadSerializer(candidato).data

        self.assertEqual(data['cpf_candidato'], '***.***.***-**')
        self.assertEqual(data['email'], 'j***@example.com')
        self.assertEqual(data['telefone'], '***********')
        self.assertIsNone(data['curriculo'])
        self.assertEqual(data['user'], {'id': 99, 'username': 'candidato'})
        self.assert_payload_omits_keys(data, self.forbidden_auth_keys)

    def test_funcionario_read_serializer_nao_expoe_auth_user_com_depth_automatico(self):
        funcionario = self.make_funcionario()

        data = FuncionarioReadSerializer(funcionario).data

        self.assertEqual(data['user'], {'id': 99, 'username': 'user1'})
        self.assertEqual(data['cpf'], '***.***.***-**')
        self.assertEqual(data['email'], 'm***@example.com')
        self.assert_payload_omits_keys(data, self.forbidden_auth_keys)

    def test_candidato_vaga_read_serializer_mascara_cpf_sem_contexto_privilegiado(self):
        candidato = Candidato(cpf_candidato='12345678901', nome='Joao')
        vaga = Vaga(id_vaga=10, titulo='Dev')
        candidatura = CandidatoVaga(
            cpf_candidato=candidato,
            id_vaga=vaga,
            status_processo='triagem',
        )

        data = CandidatoVagaReadSerializer(candidatura).data

        self.assertEqual(data['cpf_candidato'], '***.***.***-**')
        self.assertEqual(data['id_vaga']['id_vaga'], 10)
        self.assertEqual(data['status_processo'], 'triagem')
        self.assertNotIn('triagem_automatica_pontuacao', data)

    def test_contrato_read_serializer_oculta_salario_sem_contexto_privilegiado(self):
        contrato = Contrato(
            id_contrato=1,
            salario=Decimal('5000.00'),
            arquivo='contratos/contrato.pdf',
            fk_id_funcionario=Funcionario(id_funcionario=1, nome='Maria'),
        )

        data = ContratoReadSerializer(contrato).data

        self.assertIsNone(data['salario'])
        self.assertIsNone(data['arquivo'])
        self.assertEqual(data['fk_id_funcionario']['id_funcionario'], 1)
        self.assert_payload_omits_keys(data, self.forbidden_auth_keys | self.forbidden_relation_sensitive_keys)

    def test_folha_pagamento_read_serializer_oculta_arquivo_sem_contexto_privilegiado(self):
        folha = FolhaPagamento(
            id_folha=1,
            arquivo='folhas_pagamento/folha.pdf',
            fk_id_funcionario=Funcionario(id_funcionario=1, nome='Maria'),
        )

        data = FolhaPagamentoReadSerializer(folha).data

        self.assertIsNone(data['arquivo'])
        self.assertEqual(data['fk_id_funcionario']['id_funcionario'], 1)
        self.assert_payload_omits_keys(data, self.forbidden_auth_keys | self.forbidden_relation_sensitive_keys)

    def test_avaliacao_serializers_ocultam_resultado_e_comentario_sem_contexto_privilegiado(self):
        funcionario = Funcionario(id_funcionario=1, nome='Maria')
        avaliador = Funcionario(id_funcionario=2, nome='Lider')
        analise = AnaliseComportamental(
            id_analise=1,
            fk_id_funcionario=funcionario,
            resultado='Resultado confidencial',
        )
        avaliacao = AvaliacaoDesempenho(
            id_avaliacao=1,
            fk_id_funcionario=funcionario,
            fk_id_avaliador=avaliador,
            comentario='Comentario confidencial',
        )

        analise_data = AnaliseComportamentalReadSerializer(analise).data
        avaliacao_data = AvaliacaoDesempenhoReadSerializer(avaliacao).data

        self.assertIsNone(analise_data['resultado'])
        self.assertIsNone(avaliacao_data['comentario'])
        self.assertEqual(analise_data['fk_id_funcionario']['id_funcionario'], 1)
        self.assertEqual(avaliacao_data['fk_id_avaliador']['id_funcionario'], 2)
        self.assert_payload_omits_keys(
            analise_data,
            self.forbidden_auth_keys | self.forbidden_relation_sensitive_keys,
        )
        self.assert_payload_omits_keys(
            avaliacao_data,
            self.forbidden_auth_keys | self.forbidden_relation_sensitive_keys,
        )
