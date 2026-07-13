from django.db.models import Avg
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import FuncionarioComumAccessMixin, RHAdminModelViewSetMixin, ResumoActionMixin
from apps.avaliacao.api.filters import AnaliseComportamentalFilter, AvaliacaoDesempenhoFilter
from apps.avaliacao.api.serializers import (
    AnaliseComportamentalEnvioCreateSerializer,
    AnaliseComportamentalEnvioReadSerializer,
    AnaliseComportamentalReadSerializer,
    AnaliseComportamentalRespostaReadSerializer,
    AnaliseComportamentalRespostaSubmitSerializer,
    AnaliseComportamentalWriteSerializer,
    AvaliacaoDesempenhoReadSerializer,
    AvaliacaoDesempenhoWriteSerializer,
)
from apps.avaliacao.models import (
    AnaliseComportamental,
    AnaliseComportamentalResposta,
    AvaliacaoDesempenho,
)
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
        """Restringe analises ao proprio funcionario fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_funcionario_id=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        """Retorna total de analises comportamentais para RH/admin."""
        self.assert_rh_admin_access()
        return Response({
            'total_analises_comportamentais': AnaliseComportamental.objects.count(),
        })

    @action(detail=False, methods=['post'], url_path='enviar')
    def enviar(self, request):
        """Envia formulario comportamental para funcionario ou setor."""
        self.assert_rh_admin_access()
        serializer = AnaliseComportamentalEnvioCreateSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        envio = serializer.save()
        output = AnaliseComportamentalEnvioReadSerializer(
            envio,
            context=self.get_serializer_context(),
        )
        return Response(output.data, status=201)

    @action(detail=False, methods=['get'], url_path='pendentes')
    def pendentes(self, request):
        """Lista formularios pendentes do funcionario autenticado."""
        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return Response([])

        queryset = (
            AnaliseComportamentalResposta.objects
            .select_related('fk_id_envio')
            .filter(
                fk_id_funcionario_id=funcionario_id,
                status=AnaliseComportamentalResposta.STATUS_PENDENTE,
            )
            .order_by('-fk_id_envio__criado_em', 'id_resposta')
        )
        serializer = AnaliseComportamentalRespostaReadSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path=r'respostas/(?P<resposta_id>[^/.]+)/responder',
    )
    def responder(self, request, resposta_id=None):
        """Grava respostas do funcionario autenticado no formulario recebido."""
        funcionario_id = self.get_request_funcionario_id()
        resposta = (
            AnaliseComportamentalResposta.objects
            .select_related('fk_id_envio', 'fk_id_funcionario')
            .filter(
                id_resposta=resposta_id,
                fk_id_funcionario_id=funcionario_id,
                status=AnaliseComportamentalResposta.STATUS_PENDENTE,
            )
            .first()
        )
        if resposta is None:
            return Response({'detail': 'Formulario pendente nao encontrado.'}, status=404)

        serializer = AnaliseComportamentalRespostaSubmitSerializer(
            data=request.data,
            context={'resposta': resposta, **self.get_serializer_context()},
        )
        serializer.is_valid(raise_exception=True)
        resposta = serializer.save()
        output = AnaliseComportamentalRespostaReadSerializer(
            resposta,
            context=self.get_serializer_context(),
        )
        return Response(output.data)

    @action(detail=True, methods=['get'], url_path='funcionario')
    def funcionario(self, request, pk=None):
        """Retorna funcionario relacionado a analise comportamental."""
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
        """Restringe avaliacoes ao proprio funcionario fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_funcionario_id=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        """Retorna totais e media de avaliacoes para RH/admin."""
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
        """Retorna funcionario avaliado na avaliacao de desempenho."""
        avaliacao = self.get_object()
        serializer = FuncionarioReadSerializer(
            avaliacao.fk_id_funcionario,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='avaliador')
    def avaliador(self, request, pk=None):
        """Retorna funcionario avaliador da avaliacao de desempenho."""
        avaliacao = self.get_object()
        serializer = FuncionarioReadSerializer(
            avaliacao.fk_id_avaliador,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
