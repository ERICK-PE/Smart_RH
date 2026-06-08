from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import ResumoActionMixin
from apps.candidato_vaga.api.serializers import (
    CandidatoReadSerializer,
    CandidatoVagaReadSerializer,
    VagaReadSerializer,
)
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga


class CandidatoViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Candidato.objects.all().order_by('cpf_candidato')
    serializer_class = CandidatoReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = r'[^/]+'

    @action(detail=True, methods=['get'], url_path='vagas')
    def vagas(self, request, pk=None):
        candidato = self.get_object()
        serializer = CandidatoVagaReadSerializer(
            candidato.candidatovaga_set.all().order_by('id_vaga'),
            many=True,
        )
        return Response(serializer.data)


class VagaViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Vaga.objects.all().order_by('id_vaga')
    serializer_class = VagaReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='candidatos')
    def candidatos(self, request, pk=None):
        vaga = self.get_object()
        serializer = CandidatoVagaReadSerializer(
            vaga.candidatovaga_set.all().order_by('cpf_candidato'),
            many=True,
        )
        return Response(serializer.data)


class CandidatoVagaViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = CandidatoVaga.objects.all().order_by('cpf_candidato', 'id_vaga')
    serializer_class = CandidatoVagaReadSerializer
    permission_classes = [permissions.IsAuthenticated]
