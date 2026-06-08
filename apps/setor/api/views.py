from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api_mixins import ResumoActionMixin
from apps.candidato_vaga.api.serializers import VagaReadSerializer
from apps.funcionario.api.serializers import FuncionarioReadSerializer, PlanoCarreiraReadSerializer
from apps.setor.api.serializers import CargoReadSerializer, SetorReadSerializer
from apps.setor.models import Cargo, Setor


class SetorViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Setor.objects.all().order_by('id_setor')
    serializer_class = SetorReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='funcionarios')
    def funcionarios(self, request, pk=None):
        setor = self.get_object()
        serializer = FuncionarioReadSerializer(
            setor.funcionario_set.all().order_by('id_funcionario'),
            many=True,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='vagas')
    def vagas(self, request, pk=None):
        setor = self.get_object()
        serializer = VagaReadSerializer(
            setor.vaga_set.all().order_by('id_vaga'),
            many=True,
        )
        return Response(serializer.data)


class CargoViewSet(ResumoActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Cargo.objects.all().order_by('id_cargo')
    serializer_class = CargoReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='funcionarios')
    def funcionarios(self, request, pk=None):
        cargo = self.get_object()
        serializer = FuncionarioReadSerializer(
            cargo.funcionario_set.all().order_by('id_funcionario'),
            many=True,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='planos-carreira')
    def planos_carreira(self, request, pk=None):
        cargo = self.get_object()
        serializer = PlanoCarreiraReadSerializer(
            cargo.planocarreira_set.all().order_by('id_plano'),
            many=True,
        )
        return Response(serializer.data)
