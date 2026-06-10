from decimal import Decimal

from django.test import SimpleTestCase

from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AvaliacaoDesempenhoReadSerializer,
)
from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho
from apps.candidato_vaga.api.serializers import CandidatoReadSerializer, CandidatoVagaReadSerializer
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga
from apps.funcionario.api.serializers import ContratoReadSerializer
from apps.funcionario.models import Contrato, Funcionario


class SensitiveSerializerTests(SimpleTestCase):
    def test_candidato_read_serializer_mascara_dados_sem_contexto_privilegiado(self):
        candidato = Candidato(
            cpf_candidato='12345678901',
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
        self.assertEqual(data['status_processo'], 'triagem')

    def test_contrato_read_serializer_oculta_salario_sem_contexto_privilegiado(self):
        contrato = Contrato(
            id_contrato=1,
            salario=Decimal('5000.00'),
            fk_id_funcionario=Funcionario(id_funcionario=1, nome='Maria'),
        )

        data = ContratoReadSerializer(contrato).data

        self.assertIsNone(data['salario'])

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

        self.assertIsNone(AnaliseComportamentalReadSerializer(analise).data['resultado'])
        self.assertIsNone(AvaliacaoDesempenhoReadSerializer(avaliacao).data['comentario'])
