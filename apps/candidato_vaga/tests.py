from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.exceptions import PermissionDenied

from apps.candidato_vaga.api.serializers import CandidatoWriteSerializer
from apps.candidato_vaga.api.views import CandidatoAccessMixin
from apps.candidato_vaga.models import Candidato


class CandidatoWriteSerializerTests(SimpleTestCase):
    def test_curriculo_rejeita_html_simples(self):
        candidato = Candidato(cpf_candidato='12345678901')
        serializer = CandidatoWriteSerializer(
            candidato,
            data={'curriculo': '<script>alert(1)</script>'},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('curriculo', serializer.errors)


class CandidatoAccessMixinTests(SimpleTestCase):
    def test_candidato_acessa_apenas_proprio_cpf(self):
        mixin = CandidatoAccessMixin()
        mixin.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
                is_superuser=False,
                cpf_candidato='12345678901',
            )
        )

        mixin.assert_can_access_candidato('12345678901')

        with self.assertRaises(PermissionDenied):
            mixin.assert_can_access_candidato('00000000000')
