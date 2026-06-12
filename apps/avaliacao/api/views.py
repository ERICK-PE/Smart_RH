from django.db.models import Avg
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import FuncionarioComumAccessMixin, RHAdminModelViewSetMixin, ResumoActionMixin
from apps.avaliacao.api.filters import AnaliseComportamentalFilter, AvaliacaoDesempenhoFilter
from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AnaliseComportamentalWriteSerializer,
    AvaliacaoDesempenhoReadSerializer,
    AvaliacaoDesempenhoWriteSerializer,
)
from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho
from apps.funcionario.api.serializers import FuncionarioReadSerializer


class AnaliseComportamentalViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = AnaliseComportamental.objects.all().order_by('id_analise')
    serializer_class = AnaliseComportamentalReadSerializer
    write_serializer_class = AnaliseComportamentalWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = AnaliseComportamentalFilter
    filterset_fields = ['id_analise', 'fk_id_funcionario', 'data_analise']
    search_fields = ['fk_id_funcionario__nome']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_funcionario_id=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        self.assert_rh_admin_access()
        return Response({
            'total_analises_comportamentais': AnaliseComportamental.objects.count(),
        })

    @action(detail=True, methods=['get'], url_path='funcionario')
    def funcionario(self, request, pk=None):
        analise = self.get_object()
        serializer = FuncionarioReadSerializer(
            analise.fk_id_funcionario,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class AvaliacaoDesempenhoViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = AvaliacaoDesempenho.objects.all().order_by('id_avaliacao')
    serializer_class = AvaliacaoDesempenhoReadSerializer
    write_serializer_class = AvaliacaoDesempenhoWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = AvaliacaoDesempenhoFilter
    filterset_fields = ['id_avaliacao', 'fk_id_funcionario', 'fk_id_avaliador', 'categoria']
    search_fields = ['categoria', 'fk_id_funcionario__nome', 'fk_id_avaliador__nome']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_funcionario_id=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        self.assert_rh_admin_access()
        avaliacoes = self.filter_queryset(self.get_queryset())
        media_nota = avaliacoes.aggregate(media_nota=Avg('nota'))['media_nota']

        return Response({
            'total_avaliacoes_desempenho': avaliacoes.count(),
            'total_analises_comportamentais': AnaliseComportamental.objects.count(),
            'media_nota_avaliacoes_desempenho': float(media_nota) if media_nota is not None else None,
        })

    @action(detail=True, methods=['get'], url_path='funcionario')
    def funcionario(self, request, pk=None):
        avaliacao = self.get_object()
        serializer = FuncionarioReadSerializer(
            avaliacao.fk_id_funcionario,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='avaliador')
    def avaliador(self, request, pk=None):
        avaliacao = self.get_object()
        serializer = FuncionarioReadSerializer(
            avaliacao.fk_id_avaliador,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
