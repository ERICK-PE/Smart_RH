from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.response import Response

from apps.api_mixins import RHAdminAccessMixin, RHAdminModelViewSetMixin, ResumoActionMixin
from apps.candidato_vaga.api.filters import CandidatoFilter, CandidatoVagaFilter, VagaFilter
from apps.candidato_vaga.api.serializers import (
    CandidaturaCreateSerializer,
    CandidatoReadSerializer,
    CandidatoWriteSerializer,
    CandidatoVagaReadSerializer,
    CandidatoVagaWriteSerializer,
    VagaReadSerializer,
    VagaWriteSerializer,
)
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga


class CandidatoAccessMixin(RHAdminAccessMixin):
    def user_has_global_access(self):
        return self.user_has_rh_admin_access()

    def get_request_candidato_cpf(self, required=True):
        user = self.request.user

        if not user or not user.is_authenticated:
            if required:
                raise NotAuthenticated('Autenticacao obrigatoria.')
            return None

        cpf_candidato = getattr(user, 'cpf_candidato', None)
        if cpf_candidato is None:
            candidato = getattr(user, 'candidato', None)
            cpf_candidato = getattr(candidato, 'pk', None)

        if cpf_candidato is None and required:
            raise PermissionDenied('Usuario sem vinculo com candidato.')

        return cpf_candidato

    def assert_can_access_candidato(self, cpf_candidato, allow_unlinked=False):
        if self.user_has_global_access():
            return

        request_cpf = self.get_request_candidato_cpf(required=not allow_unlinked)
        if request_cpf is None and allow_unlinked:
            return

        if str(request_cpf) != str(cpf_candidato):
            raise PermissionDenied('Candidato so pode acessar os proprios dados.')


class CandidatoViewSet(CandidatoAccessMixin, ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Candidato.objects.all().order_by('cpf_candidato')
    serializer_class = CandidatoReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = r'[^/]+'
    filterset_class = CandidatoFilter
    filterset_fields = ['cpf_candidato', 'nome']
    search_fields = ['nome']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        cpf_candidato = self.get_request_candidato_cpf(required=False)
        if cpf_candidato is None:
            return queryset.none()

        return queryset.filter(pk=cpf_candidato)

    def get_candidato_object(self):
        candidato = self.get_object()
        self.assert_can_access_candidato(candidato.pk)
        return candidato

    @action(detail=False, methods=['post'], url_path='criar')
    def criar(self, request):
        serializer = CandidatoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.assert_can_access_candidato(
            serializer.validated_data['cpf_candidato'],
            allow_unlinked=True,
        )

        try:
            with transaction.atomic():
                candidato = serializer.save()
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
        filtro = request.query_params.get('filtro')
        if filtro in ['disponiveis', 'nao_candidatadas']:
            return self.vagas_disponiveis(request, pk=pk)
        if filtro in ['candidatadas', 'inscritas']:
            return self.vagas_candidatadas(request, pk=pk)

        candidato = self.get_candidato_object()
        serializer = CandidatoVagaReadSerializer(
            candidato.candidatovaga_set.all().order_by('id_vaga'),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'patch'], url_path='curriculo')
    def curriculo(self, request, pk=None):
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
        candidato = self.get_candidato_object()
        vagas_candidatadas = candidato.candidatovaga_set.values_list('id_vaga_id', flat=True)
        vagas = Vaga.objects.exclude(pk__in=vagas_candidatadas).order_by('id_vaga')
        serializer = VagaReadSerializer(vagas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='vagas-candidatadas')
    def vagas_candidatadas(self, request, pk=None):
        candidato = self.get_candidato_object()
        serializer = CandidatoVagaReadSerializer(
            candidato.candidatovaga_set.all().order_by('id_vaga'),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='candidatar-se')
    def candidatar_se(self, request, pk=None):
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
    filterset_fields = ['id_vaga', 'fk_id_setor', 'titulo']
    search_fields = ['titulo', 'descricao', 'fk_id_setor__nome']

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        self.assert_rh_admin_access()
        status_counts = (
            CandidatoVaga.objects
            .values('status_processo')
            .annotate(total=Count('cpf_candidato'))
            .order_by('status_processo')
        )
        return Response({
            'total_vagas': Vaga.objects.count(),
            'total_candidatos': Candidato.objects.count(),
            'total_candidaturas': CandidatoVaga.objects.count(),
            'candidaturas_por_status': {
                item['status_processo'] or 'sem_status': item['total']
                for item in status_counts
            },
        })

    @action(detail=True, methods=['get'], url_path='candidatos')
    def candidatos(self, request, pk=None):
        vaga = self.get_object()
        candidaturas = vaga.candidatovaga_set.all().order_by('cpf_candidato')
        if not self.user_has_global_access():
            cpf_candidato = self.get_request_candidato_cpf()
            candidaturas = candidaturas.filter(cpf_candidato_id=cpf_candidato)

        serializer = CandidatoVagaReadSerializer(
            candidaturas,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='rh/candidatos')
    def rh_candidatos(self, request, pk=None):
        self.assert_rh_admin_access()
        vaga = self.get_object()
        serializer = CandidatoVagaReadSerializer(
            vaga.candidatovaga_set.all().order_by('cpf_candidato'),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='rh/processos')
    def rh_processos(self, request, pk=None):
        self.assert_rh_admin_access()
        vaga = self.get_object()
        serializer = CandidatoVagaReadSerializer(
            vaga.candidatovaga_set.all().order_by('cpf_candidato'),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['patch'],
        url_path='rh/processos/(?P<cpf_candidato>[^/.]+)',
    )
    def rh_atualizar_processo(self, request, pk=None, cpf_candidato=None):
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


class CandidatoVagaViewSet(CandidatoAccessMixin, ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = CandidatoVaga.objects.all().order_by('cpf_candidato', 'id_vaga')
    serializer_class = CandidatoVagaReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = CandidatoVagaFilter
    filterset_fields = ['cpf_candidato', 'id_vaga', 'status_processo']
    search_fields = ['status_processo', 'id_vaga__titulo']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user_has_global_access():
            return queryset

        cpf_candidato = self.get_request_candidato_cpf(required=False)
        if cpf_candidato is None:
            return queryset.none()

        return queryset.filter(cpf_candidato_id=cpf_candidato)
