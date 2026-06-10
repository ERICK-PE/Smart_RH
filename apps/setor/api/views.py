from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import RHAdminModelViewSetMixin, ResumoActionMixin
from apps.candidato_vaga.api.serializers import VagaReadSerializer
from apps.funcionario.api.serializers import FuncionarioReadSerializer, PlanoCarreiraReadSerializer
from apps.setor.api.filters import CargoFilter, SetorFilter
from apps.setor.api.serializers import (
    CargoReadSerializer,
    CargoWriteSerializer,
    SetorReadSerializer,
    SetorWriteSerializer,
)
from apps.setor.models import Cargo, Setor


class SetorViewSet(RHAdminModelViewSetMixin, ResumoActionMixin, viewsets.ModelViewSet):
    queryset = Setor.objects.all().order_by('id_setor')
    serializer_class = SetorReadSerializer
    write_serializer_class = SetorWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = SetorFilter
    filterset_fields = ['id_setor', 'nome']
    search_fields = ['nome', 'descricao']

    @action(detail=False, methods=['get'], url_path='rh/indicadores')
    def rh_indicadores(self, request):
        self.assert_rh_admin_access()
        return Response({
            'total_setores': Setor.objects.count(),
            'total_cargos': Cargo.objects.count(),
        })

    @action(detail=True, methods=['get'], url_path='funcionarios')
    def funcionarios(self, request, pk=None):
        setor = self.get_object()
        return self.paginated_serializer_response(
            setor.funcionario_set.all().order_by('id_funcionario'),
            FuncionarioReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='vagas')
    def vagas(self, request, pk=None):
        setor = self.get_object()
        return self.paginated_serializer_response(
            setor.vaga_set.all().order_by('id_vaga'),
            VagaReadSerializer,
        )


class CargoViewSet(RHAdminModelViewSetMixin, ResumoActionMixin, viewsets.ModelViewSet):
    queryset = Cargo.objects.all().order_by('id_cargo')
    serializer_class = CargoReadSerializer
    write_serializer_class = CargoWriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = CargoFilter
    filterset_fields = ['id_cargo', 'nome']
    search_fields = ['nome', 'descricao']

    @action(detail=True, methods=['get'], url_path='funcionarios')
    def funcionarios(self, request, pk=None):
        cargo = self.get_object()
        return self.paginated_serializer_response(
            cargo.funcionario_set.all().order_by('id_funcionario'),
            FuncionarioReadSerializer,
        )

    @action(detail=True, methods=['get'], url_path='planos-carreira')
    def planos_carreira(self, request, pk=None):
        cargo = self.get_object()
        return self.paginated_serializer_response(
            cargo.planocarreira_set.all().order_by('id_plano'),
            PlanoCarreiraReadSerializer,
        )
