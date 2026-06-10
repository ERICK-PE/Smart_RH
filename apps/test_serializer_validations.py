from datetime import timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework import serializers

from apps.avaliacao.api.serializers import AvaliacaoDesempenhoWriteSerializer
from apps.funcionario.api.serializers import (
    ContratoWriteSerializer,
    FuncionarioWriteSerializer,
    PlanoCarreiraWriteSerializer,
)
from apps.funcionario.models import Contrato, Funcionario, PlanoCarreira
from apps.setor.api.serializers import CargoWriteSerializer, SetorWriteSerializer


class SerializerValidationTests(SimpleTestCase):
    def test_setor_e_cargo_rejeitam_descricao_igual_ao_nome(self):
        serializers_alvo = [
            SetorWriteSerializer(data={'nome': 'Financeiro', 'descricao': ' Financeiro '}),
            CargoWriteSerializer(data={'nome': 'Analista', 'descricao': 'Analista'}),
        ]

        for serializer in serializers_alvo:
            with self.subTest(serializer=serializer.__class__.__name__):
                self.assertFalse(serializer.is_valid())
                self.assertIn('descricao', serializer.errors)

    def test_funcionario_rejeita_data_admissao_futura(self):
        serializer = FuncionarioWriteSerializer(
            Funcionario(id_funcionario=1),
            data={'data_admissao': timezone.localdate() + timedelta(days=1)},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('data_admissao', serializer.errors)

    def test_plano_carreira_exige_descricao_ou_requisitos(self):
        serializer = PlanoCarreiraWriteSerializer(
            PlanoCarreira(id_plano=1),
            data={'descricao': '   ', 'requisitos': '   '},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('requisitos', serializer.errors)

    def test_contrato_rejeita_data_fim_anterior_a_inicio(self):
        hoje = timezone.localdate()
        serializer = ContratoWriteSerializer(
            Contrato(id_contrato=1),
            data={'data_inicio': hoje, 'data_fim': hoje - timedelta(days=1)},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('data_fim', serializer.errors)

    def test_avaliacao_rejeita_autoavaliacao_na_escrita(self):
        funcionario = SimpleNamespace(pk=1)
        serializer = AvaliacaoDesempenhoWriteSerializer()

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate({
                'fk_id_funcionario': funcionario,
                'fk_id_avaliador': funcionario,
            })

        self.assertIn('fk_id_avaliador', context.exception.detail)
