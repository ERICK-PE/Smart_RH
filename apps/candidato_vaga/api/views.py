from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.api_mixins import RHAdminAccessMixin, RHAdminModelViewSetMixin, ResumoActionMixin
from apps.candidato_vaga.api.filters import CandidatoFilter, CandidatoVagaFilter, VagaFilter
from apps.candidato_vaga.api.serializers import (
    CandidaturaCreateSerializer,
    CandidatoRegistrationSerializer,
    CandidatoReadSerializer,
    CandidatoWriteSerializer,
    CandidatoVagaRHReadSerializer,
    CandidatoVagaReadSerializer,
    CandidatoVagaWriteSerializer,
    VagaReadSerializer,
    VagaWriteSerializer,
)
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga


class CandidatoAccessMixin(RHAdminAccessMixin):
    def user_has_global_access(self):
        """Reaproveita regra RH/admin como acesso global de candidato."""
        return self.user_has_rh_admin_access()

    def get_request_candidato_cpf(self, required=True):
        """Resolve CPF do candidato autenticado por vinculo formal."""
        user = self.request.user

        if not user or not user.is_authenticated:
            if required:
                raise NotAuthenticated('Autenticacao obrigatoria.')
            return None

        try:
            candidato = getattr(user, 'candidato', None)
        except ObjectDoesNotExist:
            candidato = None

        cpf_candidato = getattr(candidato, 'pk', None)

        if cpf_candidato is None and required:
            raise PermissionDenied('Usuario sem vinculo com candidato.')

        return cpf_candidato

    def assert_can_access_candidato(self, cpf_candidato, allow_unlinked=False):
        """Garante que candidato comum acesse apenas o proprio CPF."""
        if self.user_has_global_access():
            return

        request_cpf = self.get_request_candidato_cpf(required=not allow_unlinked)
        if request_cpf is None and allow_unlinked:
            return

        if str(request_cpf) != str(cpf_candidato):
            raise PermissionDenied('Candidato so pode acessar os proprios dados.')


class CandidatoViewSet(CandidatoAccessMixin, ResumoActionMixin, viewsets.ModelViewSet):
    candidate_self_write_actions = {
        'create',
        'update',
        'partial_update',
    }

    queryset = Candidato.objects.all().order_by('cpf_candidato')
    serializer_class = CandidatoReadSerializer
    write_serializer_class = CandidatoWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    lookup_value_regex = r'[^/]+'
    filterset_class = CandidatoFilter
    filterset_fields = ['cpf_candidato', 'nome']
    search_fields = ['nome']

    def initial(self, request, *args, **kwargs):
        """Aplica politica de escrita do candidato antes da action."""
        super().initial(request, *args, **kwargs)
        self.assert_candidato_write_policy()

    def assert_candidato_write_policy(self):
        """Separa escrita do proprio candidato de exclusao RH/admin."""
        if getattr(self, 'action', None) in self.candidate_self_write_actions:
            if self.user_has_rh_admin_access():
                raise PermissionDenied('RH/admin nao cria nem edita candidato diretamente.')

        if getattr(self, 'action', None) == 'destroy':
            self.assert_rh_admin_access()

    def get_serializer_class(self):
        """Usa serializer de escrita nas acoes mutaveis do candidato."""
        if getattr(self, 'action', None) in self.candidate_self_write_actions:
            return self.write_serializer_class

        return super().get_serializer_class()

    def perform_create(self, serializer):
        """Vincula novo candidato ao usuario autenticado valido."""
        self.assert_can_access_candidato(
            serializer.validated_data['cpf_candidato'],
            allow_unlinked=True,
        )
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Restringe listagem ao proprio candidato fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        cpf_candidato = self.get_request_candidato_cpf(required=False)
        if cpf_candidato is None:
            return queryset.none()

        return queryset.filter(pk=cpf_candidato)

    def get_candidato_object(self):
        """Carrega candidato de detalhe apos validar escopo do CPF."""
        candidato = self.get_object()
        self.assert_can_access_candidato(candidato.pk)
        return candidato

    @action(
        detail=False,
        methods=['post'],
        url_path='registrar',
        permission_classes=[permissions.AllowAny],
    )
    def registrar(self, request):
        """Registra usuario e candidato em endpoint publico controlado."""
        serializer = CandidatoRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidato = serializer.save()

        return Response(
            CandidatoReadSerializer(candidato, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='criar')
    def criar(self, request):
        """Cria perfil de candidato para usuario autenticado."""
        serializer = CandidatoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.assert_can_access_candidato(
            serializer.validated_data['cpf_candidato'],
            allow_unlinked=True,
        )

        try:
            with transaction.atomic():
                candidato = serializer.save(user=request.user)
        except IntegrityError:
            return Response(
                {'cpf_candidato': ['Ja existe candidato com este CPF.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CandidatoReadSerializer(candidato, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'], url_path='vagas')
    def vagas(self, request, pk=None):
        """Lista candidaturas ou vagas filtradas do candidato."""
        filtro = request.query_params.get('filtro')
        if filtro in ['disponiveis', 'nao_candidatadas']:
            return self.vagas_disponiveis(request, pk=pk)
        if filtro in ['candidatadas', 'inscritas']:
            return self.vagas_candidatadas(request, pk=pk)

        candidato = self.get_candidato_object()
        return self.paginated_serializer_response(
            candidato.candidatovaga_set.all().order_by('id_vaga'),
            CandidatoVagaReadSerializer,
        )

    @action(detail=True, methods=['post', 'patch'], url_path='curriculo')
    def curriculo(self, request, pk=None):
        """Atualiza curriculo do proprio candidato."""
        candidato = self.get_candidato_object()
        if 'curriculo' not in request.data:
            return Response(
                {'curriculo': ['Curriculo e obrigatorio.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CandidatoWriteSerializer(
            candidato,
            data={'curriculo': request.data.get('curriculo')},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        candidato = serializer.save()
        return Response(CandidatoReadSerializer(candidato, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['get'], url_path='vagas-disponiveis')
    def vagas_disponiveis(self, request, pk=None):
        """Lista vagas em que candidato ainda nao se inscreveu."""
        candidato = self.get_candidato_object()
        vagas_candidatadas = candidato.candidatovaga_set.values_list('id_vaga_id', flat=True)
        vagas = (
            Vaga.objects
            .filter(status__in=[Vaga.STATUS_ABERTA, Vaga.STATUS_ANDAMENTO])
            .exclude(pk__in=vagas_candidatadas)
            .order_by('id_vaga')
        )
        return self.paginated_serializer_response(vagas, VagaReadSerializer)

    @action(detail=True, methods=['get'], url_path='vagas-candidatadas')
    def vagas_candidatadas(self, request, pk=None):
        """Lista candidaturas ja feitas pelo candidato."""
        candidato = self.get_candidato_object()
        return self.paginated_serializer_response(
            candidato.candidatovaga_set.all().order_by('id_vaga'),
            CandidatoVagaReadSerializer,
        )

    @action(detail=True, methods=['post'], url_path='candidatar-se')
    def candidatar_se(self, request, pk=None):
        """Cria candidatura unica do candidato para uma vaga."""
        candidato = self.get_candidato_object()
        serializer = CandidaturaCreateSerializer(
            data=request.data,
            context={'candidato': candidato},
        )
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                candidatura = serializer.save()
        except IntegrityError:
            return Response(
                {'id_vaga': ['Candidato ja inscrito nesta vaga.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CandidatoVagaReadSerializer(candidatura, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'], url_path='processos-candidaturas')
    def processos_candidaturas(self, request, pk=None):
        """Retorna processos das candidaturas do candidato."""
        return self.vagas_candidatadas(request, pk=pk)


class VagaViewSet(
    RHAdminModelViewSetMixin,
    CandidatoAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = Vaga.objects.all().order_by('id_vaga')
    serializer_class = VagaReadSerializer
    write_serializer_class = VagaWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = VagaFilter
    filterset_fields = ['id_vaga', 'fk_id_setor', 'titulo', 'status']
    search_fields = ['titulo', 'descricao', 'fk_id_setor__nome']

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        """Retorna indicadores administrativos de vagas e candidaturas."""
        self.assert_rh_admin_access()
        vagas_queryset = self.filter_queryset(self.get_queryset())
        vagas_fechadas_queryset = vagas_queryset.filter(status=Vaga.STATUS_FECHADA)
        vagas_visiveis_queryset = vagas_queryset.filter(
            status__in=[Vaga.STATUS_ABERTA, Vaga.STATUS_ANDAMENTO],
        )
        candidaturas_queryset = CandidatoVaga.objects.filter(id_vaga__in=vagas_queryset)
        candidaturas_fechadas_queryset = CandidatoVaga.objects.filter(
            id_vaga__in=vagas_fechadas_queryset,
        )
        candidaturas_visiveis_queryset = CandidatoVaga.objects.filter(
            id_vaga__in=vagas_visiveis_queryset,
        )
        vaga_status_counts = (
            vagas_queryset
            .values('status')
            .annotate(total=Count('id_vaga'))
            .order_by('status')
        )
        status_counts = (
            candidaturas_queryset
            .values('status_processo')
            .annotate(total=Count('cpf_candidato'))
            .order_by('status_processo')
        )
        status_fechadas_counts = (
            candidaturas_fechadas_queryset
            .values('status_processo')
            .annotate(total=Count('cpf_candidato'))
            .order_by('status_processo')
        )
        status_visiveis_counts = (
            candidaturas_visiveis_queryset
            .values('status_processo')
            .annotate(total=Count('cpf_candidato'))
            .order_by('status_processo')
        )
        return Response({
            'total_vagas': vagas_queryset.count(),
            'total_candidatos': Candidato.objects.count(),
            'total_candidaturas': candidaturas_queryset.count(),
            'total_candidaturas_vagas_fechadas': candidaturas_fechadas_queryset.count(),
            'total_candidaturas_vagas_visiveis': candidaturas_visiveis_queryset.count(),
            'vagas_por_status': {
                item['status'] or 'sem_status': item['total']
                for item in vaga_status_counts
            },
            'candidaturas_por_status': {
                item['status_processo'] or 'sem_status': item['total']
                for item in status_counts
            },
            'candidaturas_vagas_fechadas_por_status': {
                item['status_processo'] or 'sem_status': item['total']
                for item in status_fechadas_counts
            },
            'candidaturas_vagas_visiveis_por_status': {
                item['status_processo'] or 'sem_status': item['total']
                for item in status_visiveis_counts
            },
        })

    @action(detail=True, methods=['patch'], url_path='rh/status')
    def rh_status(self, request, pk=None):
        """Atualiza status da vaga por RH/admin."""
        self.assert_rh_admin_access()
        vaga = self.get_object()
        serializer = VagaWriteSerializer(
            vaga,
            data={'status': request.data.get('status')},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        vaga = serializer.save()
        return Response(VagaReadSerializer(vaga, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['get'], url_path='candidatos')
    def candidatos(self, request, pk=None):
        """Lista candidatos da vaga respeitando escopo do perfil."""
        vaga = self.get_object()
        candidaturas = vaga.candidatovaga_set.all().order_by('cpf_candidato')
        if not self.user_has_global_access():
            cpf_candidato = self.get_request_candidato_cpf()
            candidaturas = candidaturas.filter(cpf_candidato_id=cpf_candidato)

        return self.paginated_serializer_response(
            candidaturas,
            CandidatoVagaReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='rh/candidatos')
    def rh_candidatos(self, request, pk=None):
        """Lista candidatos aprovados pela triagem automatica para RH/admin."""
        self.assert_rh_admin_access()
        vaga = self.get_object()
        return self.paginated_serializer_response(
            vaga.candidatovaga_set
            .all()
            .filter(triagem_automatica_aprovada=True)
            .order_by('cpf_candidato'),
            CandidatoVagaRHReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='rh/processos')
    def rh_processos(self, request, pk=None):
        """Lista processos de candidatura da vaga para RH/admin."""
        self.assert_rh_admin_access()
        vaga = self.get_object()
        return self.paginated_serializer_response(
            vaga.candidatovaga_set.all().order_by('cpf_candidato'),
            CandidatoVagaRHReadSerializer,
        )

    @action(
        detail=True,
        methods=['patch'],
        url_path='rh/processos/(?P<cpf_candidato>[^/.]+)',
    )
    def rh_atualizar_processo(self, request, pk=None, cpf_candidato: str | None = None):
        """Atualiza status do processo de candidato em uma vaga."""
        self.assert_rh_admin_access()
        processo = get_object_or_404(
            CandidatoVaga,
            id_vaga_id=pk,
            cpf_candidato_id=cpf_candidato,
        )
        serializer = CandidatoVagaWriteSerializer(
            processo,
            data={'status_processo': request.data.get('status_processo')},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        processo = serializer.save()
        return Response(CandidatoVagaReadSerializer(processo, context=self.get_serializer_context()).data)


class CandidatoVagaViewSet(
    RHAdminModelViewSetMixin,
    CandidatoAccessMixin,
    ResumoActionMixin,
    viewsets.ModelViewSet,
):
    queryset = CandidatoVaga.objects.all().order_by('cpf_candidato', 'id_vaga')
    serializer_class = CandidatoVagaReadSerializer
    write_serializer_class = CandidatoVagaWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = r'[^/]+'
    filterset_class = CandidatoVagaFilter
    filterset_fields = [
        'cpf_candidato',
        'id_vaga',
        'status_processo',
        'triagem_automatica_aprovada',
    ]
    search_fields = [
        'status_processo',
        'triagem_automatica_motivo',
        'triagem_automatica_palavras_chave',
        'id_vaga__titulo',
    ]

    def parse_composite_lookup(self, lookup_value):
        """Separa lookup composto no formato cpf_candidato:id_vaga."""
        if not lookup_value or ':' not in lookup_value:
            raise NotFound('Use o formato cpf_candidato:id_vaga para detalhe do vinculo.')

        cpf_candidato, id_vaga = lookup_value.rsplit(':', 1)
        if not cpf_candidato or not id_vaga:
            raise NotFound('Use o formato cpf_candidato:id_vaga para detalhe do vinculo.')

        return cpf_candidato, id_vaga

    def get_object(self):
        """Busca vinculo candidato-vaga por lookup composto."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)

        if lookup_value:
            cpf_candidato, id_vaga = self.parse_composite_lookup(lookup_value)
            obj = (
                self.filter_queryset(self.get_queryset())
                .filter(cpf_candidato_id=cpf_candidato, id_vaga_id=id_vaga)
                .first()
            )
            if obj is None:
                raise NotFound('Vinculo candidato-vaga nao encontrado.')
            self.check_object_permissions(self.request, obj)
            return obj

        return super().get_object()

    def get_queryset(self):
        """Restringe candidaturas ao proprio candidato fora do RH/admin."""
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        cpf_candidato = self.get_request_candidato_cpf(required=False)
        if cpf_candidato is None:
            return queryset.none()

        return queryset.filter(cpf_candidato_id=cpf_candidato)
