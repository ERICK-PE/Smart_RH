from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import ResumoActionMixin
from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AvaliacaoDesempenhoReadSerializer,
)
from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho
from apps.funcionario.api.serializers import FuncionarioReadSerializer


class AnaliseComportamentalViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AnaliseComportamental.objects.all().order_by('id_analise')
    serializer_class = AnaliseComportamentalReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='funcionario')
    def funcionario(self, request, pk=None):
        analise = self.get_object()
        serializer = FuncionarioReadSerializer(analise.fk_id_funcionario)
        return Response(serializer.data)


class AvaliacaoDesempenhoViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AvaliacaoDesempenho.objects.all().order_by('id_avaliacao')
    serializer_class = AvaliacaoDesempenhoReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='funcionario')
    def funcionario(self, request, pk=None):
        avaliacao = self.get_object()
        serializer = FuncionarioReadSerializer(avaliacao.fk_id_funcionario)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='avaliador')
    def avaliador(self, request, pk=None):
        avaliacao = self.get_object()
        serializer = FuncionarioReadSerializer(avaliacao.fk_id_avaliador)
        return Response(serializer.data)
