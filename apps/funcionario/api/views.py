import mimetypes
from pathlib import Path

from django.db.models import Count
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.api_mixins import FuncionarioComumAccessMixin, RHAdminModelViewSetMixin, ResumoActionMixin
from apps.avaliacao.api.serializers import (
    AnaliseComportamentalReadSerializer,
    AvaliacaoDesempenhoReadSerializer,
    AvaliacaoDesempenhoWriteSerializer,
)
from apps.avaliacao.models import AvaliacaoDesempenho
from apps.funcionario.api.filters import ContratoFilter, FolhaPagamentoFilter, FuncionarioFilter, PlanoCarreiraFilter
from apps.funcionario.api.serializers import (
    ContratoReadSerializer,
    ContratoWriteSerializer,
    FolhaPagamentoReadSerializer,
    FolhaPagamentoWriteSerializer,
    FuncionarioAgenteDocumentoReadSerializer,
    FuncionarioAgenteDocumentoWriteSerializer,
    FuncionarioAgentePerguntaSerializer,
    FuncionarioReadSerializer,
    FuncionarioWriteSerializer,
    PlanoCarreiraReadSerializer,
    PlanoCarreiraWriteSerializer,
)
from apps.funcionario.models import Contrato, FolhaPagamento, Funcionario, FuncionarioAgenteDocumento, PlanoCarreira
from apps.funcionario.services.agente_documentos import (
    answer_question_with_openai,
    delete_important_document_file,
    load_important_document_sources,
)
from apps.funcionario.services.agente_rh import answer_rh_metrics_question_with_openai


class FuncionarioViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = (
        Funcionario.objects
        .select_related('fk_id_setor', 'fk_id_cargo', 'fk_id_cargo__fk_id_setor')
        .all()
        .order_by('id_funcionario')
    )
    serializer_class = FuncionarioReadSerializer
    write_serializer_class = FuncionarioWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    filterset_class = FuncionarioFilter
    filterset_fields = ['id_funcionario', 'fk_id_setor', 'fk_id_cargo', 'status']
    search_fields = ['nome', 'status', 'fk_id_setor__nome', 'fk_id_cargo__nome']

    def stream_document_file(self, file_field):
        """Entrega arquivo protegido sem expor caminho fisico ou URL publica."""
        if not file_field:
            raise NotFound('Arquivo nao encontrado.')

        try:
            file_handle = file_field.open('rb')
        except (FileNotFoundError, ValueError) as exc:
            raise NotFound('Arquivo nao encontrado.') from exc

        file_name = Path(file_field.name).name
        content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        return FileResponse(
            file_handle,
            as_attachment=False,
            filename=file_name,
            content_type=content_type,
        )

    def get_queryset(self):
        """Restringe listagem ao proprio funcionario fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(id_funcionario=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        """Retorna indicadores administrativos do painel de funcionarios."""
        self.assert_rh_admin_access()
        funcionarios_queryset = self.filter_queryset(self.get_queryset())
        status_counts = (
            funcionarios_queryset
            .values('status')
            .annotate(total=Count('id_funcionario'))
            .order_by('status')
        )
        return Response({
            'total_funcionarios': funcionarios_queryset.count(),
            'total_contratos': Contrato.objects.count(),
            'total_folhas_pagamento': FolhaPagamento.objects.count(),
            'total_planos_carreira': PlanoCarreira.objects.count(),
            'funcionarios_por_status': {
                item['status'] or 'sem_status': item['total']
                for item in status_counts
            },
        })

    @action(detail=True, methods=['get'], url_path='contratos')
    def contratos(self, request, pk=None):
        """Lista contratos vinculados ao funcionario informado."""
        funcionario = self.get_object()
        return self.paginated_serializer_response(
            funcionario.contrato_set.all().order_by('id_contrato'),
            ContratoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='rh/perfil')
    def rh_perfil(self, request, pk=None):
        """Retorna perfil completo do funcionario para RH/admin."""
        self.assert_rh_admin_access()
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'patch'], url_path='rh/folha-pagamento')
    def rh_folha_pagamento(self, request, pk=None):
        """Cria folha de pagamento para funcionario por upload RH/admin."""
        self.assert_rh_admin_access()
        funcionario = self.get_object()
        data = request.data.copy()
        data['fk_id_funcionario'] = funcionario.pk
        serializer = FolhaPagamentoWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        folha = serializer.save()
        return Response(
            FolhaPagamentoReadSerializer(folha, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='rh/inativar')
    def rh_inativar(self, request, pk=None):
        """Inativa funcionario preservando historico cadastral."""
        self.assert_rh_admin_access()
        funcionario = self.get_object()
        funcionario.status = Funcionario.STATUS_INATIVO
        funcionario.save(update_fields=['status'])
        serializer = self.get_serializer(funcionario)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='rh/reativar')
    def rh_reativar(self, request, pk=None):
        """Reativa funcionario previamente inativado."""
        self.assert_rh_admin_access()
        funcionario = self.get_object()
        funcionario.status = Funcionario.STATUS_ATIVO
        funcionario.save(update_fields=['status'])
        serializer = self.get_serializer(funcionario)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='meus-dados')
    def meus_dados(self, request, pk=None):
        """Retorna dados do proprio funcionario autenticado."""
        funcionario = self.get_funcionario_comum_object()
        serializer = self.get_serializer(funcionario)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='meus-contratos')
    def meus_contratos(self, request, pk=None):
        """Lista contratos do proprio funcionario autenticado."""
        funcionario = self.get_funcionario_comum_object()
        return self.paginated_serializer_response(
            funcionario.contrato_set.all().order_by('id_contrato'),
            ContratoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path=r'meus-contratos/(?P<id_contrato>[^/.]+)/arquivo')
    def meu_contrato_arquivo(self, request, pk=None, id_contrato=None):
        """Permite ao funcionario visualizar arquivo do proprio contrato."""
        funcionario = self.get_funcionario_comum_object()
        contrato = get_object_or_404(
            funcionario.contrato_set.all(),
            pk=id_contrato,
        )
        return self.stream_document_file(contrato.arquivo)

    @action(detail=True, methods=['get'], url_path='meus-contratos-pdf')
    def meus_contratos_pdf(self, request, pk=None):
        """Sinaliza ponto futuro para PDFs de contrato do funcionario."""
        self.assert_can_access_funcionario(pk)
        return Response(
            {'detail': 'Arquivos PDF de contrato ainda nao foram modelados.'},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    @action(detail=True, methods=['get'], url_path='folha-pagamento')
    def folha_pagamento(self, request, pk=None):
        """Lista folhas de pagamento do proprio funcionario."""
        funcionario = self.get_funcionario_comum_object()
        return self.paginated_serializer_response(
            funcionario.folhapagamento_set.all().order_by('-criado_em', '-id_folha'),
            FolhaPagamentoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path=r'folha-pagamento/(?P<id_folha>[^/.]+)/arquivo')
    def folha_pagamento_arquivo(self, request, pk=None, id_folha=None):
        """Permite ao funcionario visualizar arquivo da propria folha."""
        funcionario = self.get_funcionario_comum_object()
        folha = get_object_or_404(
            funcionario.folhapagamento_set.all(),
            pk=id_folha,
        )
        return self.stream_document_file(folha.arquivo)

    @action(detail=True, methods=['get'], url_path='minhas-avaliacoes-desempenho')
    def minhas_avaliacoes_desempenho(self, request, pk=None):
        """Lista avaliacoes de desempenho do proprio funcionario."""
        funcionario = self.get_funcionario_comum_object()
        return self.paginated_serializer_response(
            funcionario.avaliacaodesempenho_set.all().order_by('id_avaliacao'),
            AvaliacaoDesempenhoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='meu-plano-carreira')
    def meu_plano_carreira(self, request, pk=None):
        """Lista apenas o plano de carreira mais recente do cargo do funcionario."""
        funcionario = self.get_funcionario_comum_object()
        return self.paginated_serializer_response(
            PlanoCarreira.objects.filter(fk_id_cargo_id=funcionario.fk_id_cargo_id).order_by('-id_plano')[:1],
            PlanoCarreiraReadSerializer,
        )

    @action(detail=False, methods=['get'], url_path='lideranca/funcionarios-setor')
    def lideranca_funcionarios_setor(self, request):
        """Lista funcionarios do setor da lideranca autenticada."""
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
        """Lista planos de carreira ligados ao setor da lideranca."""
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
        """Lista planos de carreira do funcionario no escopo da lideranca."""
        funcionario = self.get_funcionario_setor_lideranca(pk)
        return self.paginated_serializer_response(
            PlanoCarreira.objects.filter(fk_id_cargo=funcionario.fk_id_cargo).order_by('id_plano'),
            PlanoCarreiraReadSerializer,
        )

    @action(detail=True, methods=['post'], url_path='lideranca/criar-plano-carreira')
    def lideranca_criar_plano_carreira(self, request, pk=None):
        """Cria plano de carreira para funcionario no escopo da lideranca."""
        funcionario = self.get_funcionario_setor_lideranca(pk)
        data = request.data.copy()
        data['fk_id_cargo'] = funcionario.fk_id_cargo_id

        serializer = PlanoCarreiraWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        save_kwargs = {}
        if not self.user_has_global_access():
            save_kwargs['fk_id_criador'] = self.get_request_funcionario()
        plano = serializer.save(**save_kwargs)

        return Response(
            PlanoCarreiraReadSerializer(plano, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=['patch'],
        url_path='lideranca/planos-carreira/(?P<plano_id>[^/.]+)/editar',
    )
    def lideranca_editar_plano_carreira(self, request, pk=None, plano_id: int | None = None):
        """Edita plano de carreira no escopo permitido a lideranca."""
        funcionario = self.get_funcionario_setor_lideranca(pk)
        plano = get_object_or_404(
            PlanoCarreira,
            pk=plano_id,
            fk_id_cargo=funcionario.fk_id_cargo,
        )
        self.assert_can_edit_lideranca_plano(plano)

        data = request.data.copy()
        data['fk_id_cargo'] = funcionario.fk_id_cargo_id

        serializer = PlanoCarreiraWriteSerializer(
            plano,
            data=data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        plano = serializer.save()

        return Response(
            PlanoCarreiraReadSerializer(plano, context=self.get_serializer_context()).data
        )

    @action(detail=True, methods=['post'], url_path='lideranca/criar-avaliacao-desempenho')
    def lideranca_criar_avaliacao_desempenho(self, request, pk=None):
        """Cria avaliacao de desempenho no escopo da lideranca."""
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

    @action(detail=True, methods=['get'], url_path='lideranca/avaliacoes-desempenho')
    def lideranca_avaliacoes_desempenho(self, request, pk=None):
        """Lista avaliacoes do funcionario no escopo da lideranca."""
        funcionario = self.get_funcionario_setor_lideranca(pk)
        return self.paginated_serializer_response(
            funcionario.avaliacaodesempenho_set.all().order_by('-data_avaliacao', '-id_avaliacao'),
            AvaliacaoDesempenhoReadSerializer,
        )

    @action(
        detail=True,
        methods=['patch'],
        url_path='lideranca/avaliacoes-desempenho/(?P<avaliacao_id>[^/.]+)/editar',
    )
    def lideranca_editar_avaliacao_desempenho(self, request, pk=None, avaliacao_id: int | None = None):
        """Edita avaliacao de desempenho no escopo permitido a lideranca."""
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
        """Lista analises comportamentais vinculadas ao funcionario."""
        funcionario = self.get_object()
        return self.paginated_serializer_response(
            funcionario.analisecomportamental_set.all().order_by('id_analise'),
            AnaliseComportamentalReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='avaliacoes-recebidas')
    def avaliacoes_recebidas(self, request, pk=None):
        """Lista avaliacoes recebidas pelo funcionario."""
        funcionario = self.get_object()
        return self.paginated_serializer_response(
            funcionario.avaliacaodesempenho_set.all().order_by('id_avaliacao'),
            AvaliacaoDesempenhoReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='avaliacoes-realizadas')
    def avaliacoes_realizadas(self, request, pk=None):
        """Lista avaliacoes realizadas pelo funcionario como avaliador."""
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
        """Restringe planos ao cargo do funcionario fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_cargo__funcionario__id_funcionario=funcionario_id)

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        """Retorna total de planos de carreira para RH/admin."""
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
        """Cria plano de carreira administrativo para funcionario alvo."""
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
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    filterset_class = ContratoFilter
    filterset_fields = ['id_contrato', 'fk_id_funcionario', 'tipo_contrato']
    search_fields = ['tipo_contrato', 'fk_id_funcionario__nome']

    def get_queryset(self):
        """Restringe contratos ao proprio funcionario fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_funcionario_id=funcionario_id)

    @action(detail=True, methods=['post', 'patch'], url_path='rh/arquivo')
    def rh_arquivo(self, request, pk=None):
        """Atualiza arquivo de contrato pelo RH/admin."""
        self.assert_rh_admin_access()
        contrato = self.get_object()
        if 'arquivo' not in request.data:
            return Response(
                {'arquivo': ['Arquivo do contrato e obrigatorio.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ContratoWriteSerializer(
            contrato,
            data={'arquivo': request.data.get('arquivo')},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        contrato = serializer.save()
        return Response(ContratoReadSerializer(contrato, context=self.get_serializer_context()).data)


class FolhaPagamentoViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = FolhaPagamento.objects.all().order_by('-criado_em', '-id_folha')
    serializer_class = FolhaPagamentoReadSerializer
    write_serializer_class = FolhaPagamentoWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    filterset_class = FolhaPagamentoFilter
    filterset_fields = ['id_folha', 'fk_id_funcionario', 'competencia']
    search_fields = ['competencia', 'fk_id_funcionario__nome']

    def get_queryset(self):
        """Restringe folhas ao proprio funcionario fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        funcionario_id = self.get_request_funcionario_id(required=False)
        if funcionario_id is None:
            return queryset.none()

        return queryset.filter(fk_id_funcionario_id=funcionario_id)


class FuncionarioAgenteDocumentoViewSet(
    RHAdminModelViewSetMixin,
    FuncionarioComumAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = FuncionarioAgenteDocumento.objects.all().order_by('-criado_em')
    serializer_class = FuncionarioAgenteDocumentoReadSerializer
    write_serializer_class = FuncionarioAgenteDocumentoWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    filterset_fields = ['id_documento', 'titulo', 'ativo']
    search_fields = ['titulo']

    def initial(self, request, *args, **kwargs):
        """Permite pergunta ao funcionario e restringe gestao documental ao RH."""
        super().initial(request, *args, **kwargs)
        if getattr(self, 'action', None) != 'perguntar':
            self.assert_rh_admin_access()

    def perform_create(self, serializer):
        """Registra usuario RH/admin que enviou documento."""
        serializer.save(criado_por=self.request.user)

    def perform_destroy(self, instance):
        """Remove cadastro e arquivo fisico vinculado ao documento."""
        arquivo = instance.arquivo.name
        super().perform_destroy(instance)
        delete_important_document_file(arquivo)

    @action(detail=False, methods=['post'], url_path='perguntar')
    def perguntar(self, request):
        """Responde pergunta conforme perfil: RH por metricas, demais por documentos."""
        user_is_rh_admin = self.user_has_global_access()
        if not user_is_rh_admin:
            self.get_request_funcionario_id()

        serializer = FuncionarioAgentePerguntaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pergunta = serializer.validated_data['pergunta']

        if user_is_rh_admin:
            try:
                resposta = answer_rh_metrics_question_with_openai(pergunta)
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            return Response({
                'pergunta': pergunta,
                **resposta,
            })

        documentos = load_important_document_sources()
        if not documentos:
            return Response(
                {'detail': 'Nenhum documento ativo e legivel cadastrado para o agente.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            resposta = answer_question_with_openai(pergunta, documentos)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            'pergunta': pergunta,
            **resposta,
        })
