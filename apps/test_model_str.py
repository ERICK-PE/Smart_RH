from decimal import Decimal

from django.test import SimpleTestCase

from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga
from apps.funcionario.models import Contrato, FolhaPagamento, Funcionario, PlanoCarreira
from apps.setor.models import Cargo, Setor


class ModelStrTests(SimpleTestCase):
    def test_setor_e_cargo_usam_nome(self):
        self.assertEqual(str(Setor(nome='Tecnologia')), 'Tecnologia')
        self.assertEqual(str(Cargo(nome='Analista')), 'Analista')

    def test_funcionario_usa_nome_sem_dados_sensiveis(self):
        funcionario = Funcionario(
            nome='Maria Silva',
            cpf='123.456.789-00',
            email='maria@example.com',
            telefone='11999999999',
        )

        texto = str(funcionario)

        self.assertEqual(texto, 'Maria Silva')
        self.assertNotIn('123.456.789-00', texto)
        self.assertNotIn('maria@example.com', texto)
        self.assertNotIn('11999999999', texto)

    def test_plano_carreira_e_contrato_usam_identificador_sem_salario(self):
        plano = PlanoCarreira(id_plano=7, descricao='Plano lideranca')
        contrato = Contrato(id_contrato=3, salario=Decimal('4500.00'))
        folha = FolhaPagamento(id_folha=5, arquivo='folhas_pagamento/folha.pdf')

        self.assertEqual(str(plano), 'Plano de carreira 7')
        self.assertEqual(str(contrato), 'Contrato 3')
        self.assertEqual(str(folha), 'Folha de pagamento 5')
        self.assertNotIn('4500', str(contrato))
        self.assertNotIn('folha.pdf', str(folha))

    def test_candidato_e_vaga_usam_nome_titulo_sem_campos_sensiveis(self):
        candidato = Candidato(
            cpf_candidato='12345678901',
            nome='Joao Candidato',
            email='joao@example.com',
            telefone='11988887777',
            curriculo='Experiencia sensivel',
        )
        vaga = Vaga(id_vaga=9, titulo='Dev Backend', descricao='Vaga interna')

        self.assertEqual(str(candidato), 'Joao Candidato')
        self.assertEqual(str(vaga), 'Dev Backend')
        self.assertNotIn('12345678901', str(candidato))
        self.assertNotIn('joao@example.com', str(candidato))
        self.assertNotIn('Experiencia sensivel', str(candidato))

    def test_candidato_vaga_usa_ids_sem_carregar_relacionamentos(self):
        candidatura = CandidatoVaga(
            cpf_candidato_id='12345678901',
            id_vaga_id=9,
            status_processo='triagem',
        )

        self.assertEqual(str(candidatura), 'Candidato 12345678901 - Vaga 9')

    def test_avaliacoes_usam_identificador_sem_resultado_ou_comentario(self):
        analise = AnaliseComportamental(id_analise=4, resultado='Perfil confidencial')
        avaliacao = AvaliacaoDesempenho(id_avaliacao=5, comentario='Comentario confidencial')

        self.assertEqual(str(analise), 'Analise comportamental 4')
        self.assertEqual(str(avaliacao), 'Avaliacao de desempenho 5')
        self.assertNotIn('Perfil confidencial', str(analise))
        self.assertNotIn('Comentario confidencial', str(avaliacao))
