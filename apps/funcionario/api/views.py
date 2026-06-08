from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import ResumoActionMixin
from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AvaliacaoDesempenhoReadSerializer,
)
from apps.funcionario.api.serializers import (
    ContratoReadSerializer,
    FuncionarioReadSerializer,
    PlanoCarreiraReadSerializer,
)
from apps.funcionario.models import Contrato, Funcionario, PlanoCarreira


class FuncionarioViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Funcionario.objects.all().order_by('id_funcionario')
    serializer_class = FuncionarioReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='contratos')
    def contratos(self, request, pk=None):
        funcionario = self.get_object()
        serializer = ContratoReadSerializer(
            funcionario.contrato_set.all().order_by('id_contrato'),
            many=True,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='analises-comportamentais')
    def analises_comportamentais(self, request, pk=None):
        funcionario = self.get_object()
        serializer = AnaliseComportamentalReadSerializer(
            funcionario.analisecomportamental_set.all().order_by('id_analise'),
            many=True,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='avaliacoes-recebidas')
    def avaliacoes_recebidas(self, request, pk=None):
        funcionario = self.get_object()
        serializer = AvaliacaoDesempenhoReadSerializer(
            funcionario.avaliacaodesempenho_set.all().order_by('id_avaliacao'),
            many=True,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='avaliacoes-realizadas')
    def avaliacoes_realizadas(self, request, pk=None):
        funcionario = self.get_object()
        serializer = AvaliacaoDesempenhoReadSerializer(
            funcionario.avaliacaodesempenho_fk_id_avaliador_set.all().order_by('id_avaliacao'),
            many=True,
        )
        return Response(serializer.data)


class PlanoCarreiraViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PlanoCarreira.objects.all().order_by('id_plano')
    serializer_class = PlanoCarreiraReadSerializer
    permission_classes = [permissions.IsAuthenticated]


class ContratoViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Contrato.objects.all().order_by('id_contrato')
    serializer_class = ContratoReadSerializer
    permission_classes = [permissions.IsAuthenticated]
