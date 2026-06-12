from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import FuncionarioComumAccessMixin, RHAdminModelViewSetMixin, ResumoActionMixin
from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AvaliacaoDesempenhoReadSerializer,
    AvaliacaoDesempenhoWriteSerializer,
)
from apps.avaliacao.models import AvaliacaoDesempenho
from apps.funcionario.api.filters import ContratoFilter, FuncionarioFilter, PlanoCarreiraFilter
from apps.funcionario.api.serializers import (
    ContratoReadSerializer,
    ContratoWriteSerializer,
    FuncionarioReadSerializer,
    FuncionarioWriteSerializer,
    PlanoCarreiraReadSerializer,
    PlanoCarreiraWriteSerializer,
)
from apps.funcionario.models import Contrato, Funcionario, PlanoCarreira


class FuncionarioViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = Funcionario.objects.all().order_by('id_funcionario')
    serializer_class = FuncionarioReadSerializer
    write_serializer_class = FuncionarioWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = FuncionarioFilter
    filterset_fields = ['id_funcionario', 'fk_id_setor', 'fk_id_cargo', 'status']
    search_fields = ['nome', 'status', 'fk_id_setor__nome', 'fk_id_cargo__nome']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(id_funcionario=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        self.assert_rh_admin_access()
        status_counts = (
            Funcionario.objects
            .values('status')
            .annotate(total=Count('id_funcionario'))
            .order_by('status')
        )
        return Response({
            'total_funcionarios': Funcionario.objects.count(),
            'total_contratos': Contrato.objects.count(),
            'total_planos_carreira': PlanoCarreira.objects.count(),
            'funcionarios_por_status': {
                item['status'] or 'sem_status': item['total']
                for item in status_counts
            },
        })

    @action(detail=True, methods=['get'], url_path='contratos')
    def contratos(self, request, pk=None):
        funcionario = self.get_object()
        return self.paginated_serializer_response(
            funcionario.contrato_set.all().order_by('id_contrato'),
            ContratoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='rh/perfil')
    def rh_perfil(self, request, pk=None):
        self.assert_rh_admin_access()
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'patch'], url_path='rh/folha-pagamento')
    def rh_folha_pagamento(self, request, pk=None):
        self.assert_rh_admin_access()
        self.get_object()
        return Response(
            {'detail': 'Arquivo de folha de pagamento ainda nao foi modelado.'},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    @action(detail=True, methods=['post'], url_path='rh/inativar')
    def rh_inativar(self, request, pk=None):
        self.assert_rh_admin_access()
        funcionario = self.get_object()
        funcionario.status = Funcionario.STATUS_INATIVO
        funcionario.save(update_fields=['status'])
        serializer = self.get_serializer(funcionario)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='rh/reativar')
    def rh_reativar(self, request, pk=None):
        self.assert_rh_admin_access()
        funcionario = self.get_object()
        funcionario.status = Funcionario.STATUS_ATIVO
        funcionario.save(update_fields=['status'])
        serializer = self.get_serializer(funcionario)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='meus-dados')
    def meus_dados(self, request, pk=None):
        funcionario = self.get_funcionario_comum_object()
        serializer = self.get_serializer(funcionario)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='meus-contratos')
    def meus_contratos(self, request, pk=None):
        funcionario = self.get_funcionario_comum_object()
        return self.paginated_serializer_response(
            funcionario.contrato_set.all().order_by('id_contrato'),
            ContratoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='meus-contratos-pdf')
    def meus_contratos_pdf(self, request, pk=None):
        self.assert_can_access_funcionario(pk)
        return Response(
            {'detail': 'Arquivos PDF de contrato ainda nao foram modelados.'},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    @action(detail=True, methods=['get'], url_path='folha-pagamento')
    def folha_pagamento(self, request, pk=None):
        self.assert_can_access_funcionario(pk)
        return Response(
            {'detail': 'Folha de pagamento ainda nao foi modelada.'},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    @action(detail=True, methods=['get'], url_path='minhas-avaliacoes-desempenho')
    def minhas_avaliacoes_desempenho(self, request, pk=None):
        funcionario = self.get_funcionario_comum_object()
        return self.paginated_serializer_response(
            funcionario.avaliacaodesempenho_set.all().order_by('id_avaliacao'),
            AvaliacaoDesempenhoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='meu-plano-carreira')
    def meu_plano_carreira(self, request, pk=None):
        funcionario = self.get_funcionario_comum_object()
        return self.paginated_serializer_response(
            PlanoCarreira.objects.filter(fk_id_cargo=funcionario.fk_id_cargo).order_by('id_plano'),
            PlanoCarreiraReadSerializer,
        )

    @action(detail=False, methods=['get'], url_path='lideranca/funcionarios-setor')
    def lideranca_funcionarios_setor(self, request):
        self.assert_lideranca_access()
        if self.user_has_global_access():
            return self.paginated_serializer_response(
                Funcionario.objects.all().order_by('id_funcionario'),
                FuncionarioReadSerializer,
            )

        lider = self.get_request_funcionario()
        return self.paginated_serializer_response(
            Funcionario.objects.filter(fk_id_setor=lider.fk_id_setor).order_by('id_funcionario'),
            FuncionarioReadSerializer,
        )

    @action(detail=False, methods=['get'], url_path='lideranca/planos-carreira-setor')
    def lideranca_planos_carreira_setor(self, request):
        self.assert_lideranca_access()
        if self.user_has_global_access():
            return self.paginated_serializer_response(
                PlanoCarreira.objects.all().order_by('id_plano'),
                PlanoCarreiraReadSerializer,
            )

        lider = self.get_request_funcionario()
        return self.paginated_serializer_response(
            PlanoCarreira.objects.filter(
                fk_id_cargo__funcionario__fk_id_setor=lider.fk_id_setor,
            ).distinct().order_by('id_plano'),
            PlanoCarreiraReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='lideranca/planos-carreira')
    def lideranca_planos_carreira(self, request, pk=None):
        funcionario = self.get_funcionario_setor_lideranca(pk)
        return self.paginated_serializer_response(
            PlanoCarreira.objects.filter(fk_id_cargo=funcionario.fk_id_cargo).order_by('id_plano'),
            PlanoCarreiraReadSerializer,
        )

    @action(detail=True, methods=['post'], url_path='lideranca/criar-plano-carreira')
    def lideranca_criar_plano_carreira(self, request, pk=None):
        funcionario = self.get_funcionario_setor_lideranca(pk)
        data = request.data.copy()
        data['fk_id_cargo'] = funcionario.fk_id_cargo_id

        serializer = PlanoCarreiraWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        plano = serializer.save()

        return Response(
            PlanoCarreiraReadSerializer(plano, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='lideranca/criar-avaliacao-desempenho')
    def lideranca_criar_avaliacao_desempenho(self, request, pk=None):
        funcionario = self.get_funcionario_setor_lideranca(pk)
        data = request.data.copy()
        data['fk_id_funcionario'] = funcionario.pk

        if self.user_has_global_access():
            if not data.get('fk_id_avaliador'):
                return Response(
                    {'fk_id_avaliador': 'Avaliador e obrigatorio para acesso administrativo.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            data['fk_id_avaliador'] = self.get_request_funcionario().pk

        serializer = AvaliacaoDesempenhoWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        avaliacao = serializer.save()

        return Response(
            AvaliacaoDesempenhoReadSerializer(avaliacao, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=['patch'],
        url_path='lideranca/avaliacoes-desempenho/(?P<avaliacao_id>[^/.]+)/editar',
    )
    def lideranca_editar_avaliacao_desempenho(self, request, pk=None, avaliacao_id: int | None = None):
        funcionario = self.get_funcionario_setor_lideranca(pk)
        avaliacao = get_object_or_404(
            AvaliacaoDesempenho,
            pk=avaliacao_id,
            fk_id_funcionario=funcionario,
        )
        self.assert_can_edit_lideranca_avaliacao(avaliacao)

        data = request.data.copy()
        data['fk_id_funcionario'] = funcionario.pk
        data['fk_id_avaliador'] = avaliacao.fk_id_avaliador_id

        serializer = AvaliacaoDesempenhoWriteSerializer(
            avaliacao,
            data=data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        avaliacao = serializer.save()

        return Response(
            AvaliacaoDesempenhoReadSerializer(avaliacao, context=self.get_serializer_context()).data
        )

    @action(detail=True, methods=['get'], url_path='analises-comportamentais')
    def analises_comportamentais(self, request, pk=None):
        funcionario = self.get_object()
        return self.paginated_serializer_response(
            funcionario.analisecomportamental_set.all().order_by('id_analise'),
            AnaliseComportamentalReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='avaliacoes-recebidas')
    def avaliacoes_recebidas(self, request, pk=None):
        funcionario = self.get_object()
        return self.paginated_serializer_response(
            funcionario.avaliacaodesempenho_set.all().order_by('id_avaliacao'),
            AvaliacaoDesempenhoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='avaliacoes-realizadas')
    def avaliacoes_realizadas(self, request, pk=None):
        funcionario = self.get_object()
        return self.paginated_serializer_response(
            funcionario.avaliacaodesempenho_fk_id_avaliador_set.all().order_by('id_avaliacao'),
            AvaliacaoDesempenhoReadSerializer,
        )


class PlanoCarreiraViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = PlanoCarreira.objects.all().order_by('id_plano')
    serializer_class = PlanoCarreiraReadSerializer
    write_serializer_class = PlanoCarreiraWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PlanoCarreiraFilter
    filterset_fields = ['id_plano', 'fk_id_cargo']
    search_fields = ['descricao', 'requisitos', 'fk_id_cargo__nome']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_cargo__funcionario__id_funcionario=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        self.assert_rh_admin_access()
        return Response({
            'total_planos_carreira': PlanoCarreira.objects.count(),
        })

    @action(
        detail=False,
        methods=['post'],
        url_path='rh/criar-para-funcionario/(?P<funcionario_id>[^/.]+)',
    )
    def rh_criar_para_funcionario(self, request, funcionario_id: int | None = None):
        self.assert_rh_admin_access()
        get_object_or_404(Funcionario, pk=funcionario_id)

        if not request.data.get('fk_id_cargo'):
            return Response(
                {'fk_id_cargo': 'Informe o cargo superior para vincular ao plano.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PlanoCarreiraWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plano = serializer.save()
        return Response(
            PlanoCarreiraReadSerializer(plano, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class ContratoViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = Contrato.objects.all().order_by('id_contrato')
    serializer_class = ContratoReadSerializer
    write_serializer_class = ContratoWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = ContratoFilter
    filterset_fields = ['id_contrato', 'fk_id_funcionario', 'tipo_contrato']
    search_fields = ['tipo_contrato', 'fk_id_funcionario__nome']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_funcionario_id=funcionario_id)

    @action(detail=True, methods=['post', 'patch'], url_path='rh/arquivo')
    def rh_arquivo(self, request, pk=None):
        self.assert_rh_admin_access()
        self.get_object()
        return Response(
            {'detail': 'Arquivo de contrato ainda nao foi modelado.'},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
