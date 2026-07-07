from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from Smart_RH.api_dashboard import SmartRHDashboardRHView


class FakeValuesQuerySet:
    def __init__(self, rows):
        self.rows = rows

    def annotate(self, **kwargs):
        return self

    def order_by(self, *fields):
        return self.rows


class FakeQuerySet:
    def __init__(self, count=0, groups=None, aggregate=None):
        self.count_value = count
        self.groups = groups or {}
        self.aggregate_value = aggregate or {}

    def select_related(self, *fields):
        return self

    def all(self):
        return self

    def filter(self, *args, **kwargs):
        return self

    def exclude(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def count(self):
        return self.count_value

    def values(self, *fields):
        return FakeValuesQuerySet(self.groups.get(fields, []))

    def aggregate(self, **kwargs):
        return self.aggregate_value


class DashboardRHAPITests(SimpleTestCase):
    def make_user(self, is_staff=True):
        return SimpleNamespace(
            is_authenticated=True,
            is_staff=is_staff,
            is_superuser=False,
            pk=None,
            has_perm=lambda permission: False,
        )

    def test_dashboard_rh_bloqueia_usuario_sem_perfil_rh(self):
        request = APIRequestFactory().get('/api/dashboard/rh/')
        force_authenticate(request, user=self.make_user(is_staff=False))

        response = SmartRHDashboardRHView.as_view()(request)

        self.assertEqual(response.status_code, 403)

    def test_dashboard_rh_retorna_contrato_agregado_sem_pii(self):
        request = APIRequestFactory().get('/api/dashboard/rh/')
        force_authenticate(request, user=self.make_user())

        funcionarios = FakeQuerySet(
            count=4,
            groups={
                ('fk_id_setor__nome',): [{'fk_id_setor__nome': 'Tecnologia', 'total': 3}],
                ('fk_id_cargo__nome',): [{'fk_id_cargo__nome': 'Analista', 'total': 2}],
                ('status',): [{'status': 'ativo', 'total': 4}],
            },
        )
        vagas = FakeQuerySet(
            count=2,
            groups={
                ('status',): [{'status': 'aberta', 'total': 1}, {'status': 'fechada', 'total': 1}],
            },
        )
        candidaturas = FakeQuerySet(
            count=5,
            groups={
                ('id_vaga', 'id_vaga__titulo'): [
                    {'id_vaga': 1, 'id_vaga__titulo': 'Dev', 'total': 5},
                ],
            },
        )
        candidatos = FakeQuerySet(count=3)
        avaliacoes = FakeQuerySet(aggregate={'media': 8.5})

        with (
            patch('Smart_RH.api_dashboard.Funcionario.objects', funcionarios),
            patch('Smart_RH.api_dashboard.Vaga.objects', vagas),
            patch('Smart_RH.api_dashboard.CandidatoVaga.objects', candidaturas),
            patch('Smart_RH.api_dashboard.Candidato.objects', candidatos),
            patch('Smart_RH.api_dashboard.AvaliacaoDesempenho.objects', avaliacoes),
        ):
            response = SmartRHDashboardRHView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {'resumo', 'empresa', 'avaliacoes', 'recrutamento'})
        self.assertIn('funcionarios_ativos', response.data['resumo'])
        self.assertIn('funcionarios_por_setor', response.data['empresa'])
        self.assertIn('planos_carreira_cobertura', response.data['avaliacoes'])
        self.assertIn('funil', response.data['recrutamento'])
        self.assertNotIn('cpf', str(response.data).lower())
        self.assertNotIn('email', str(response.data).lower())
