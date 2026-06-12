from django.db.models import Q
from django_filters import rest_framework as filters

from apps.funcionario.models import Contrato, Funcionario, PlanoCarreira


class FuncionarioFilter(filters.FilterSet):
    nome = filters.CharFilter(field_name='nome', lookup_expr='icontains')
    setor = filters.NumberFilter(field_name='fk_id_setor')
    cargo = filters.NumberFilter(field_name='fk_id_cargo')
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')
    setor_nome = filters.CharFilter(field_name='fk_id_setor__nome', lookup_expr='icontains')
    cargo_nome = filters.CharFilter(field_name='fk_id_cargo__nome', lookup_expr='icontains')
    data_admissao_inicio = filters.DateFilter(field_name='data_admissao', lookup_expr='gte')
    data_admissao_fim = filters.DateFilter(field_name='data_admissao', lookup_expr='lte')

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'nome',
            'setor',
            'cargo',
            'status',
            'setor_nome',
            'cargo_nome',
            'data_admissao_inicio',
            'data_admissao_fim',
        ]


class PlanoCarreiraFilter(filters.FilterSet):
    cargo = filters.NumberFilter(field_name='fk_id_cargo')
    cargo_nome = filters.CharFilter(field_name='fk_id_cargo__nome', lookup_expr='icontains')
    texto = filters.CharFilter(method='filter_texto')

    class Meta:
        model = PlanoCarreira
        fields = ['id_plano', 'cargo', 'cargo_nome', 'texto']

    def filter_texto(self, queryset, name, value):
        """Busca texto em descricao ou requisitos do plano."""
        return queryset.filter(Q(descricao__icontains=value) | Q(requisitos__icontains=value))


class ContratoFilter(filters.FilterSet):
    funcionario = filters.NumberFilter(field_name='fk_id_funcionario')
    funcionario_nome = filters.CharFilter(field_name='fk_id_funcionario__nome', lookup_expr='icontains')
    tipo_contrato = filters.CharFilter(field_name='tipo_contrato', lookup_expr='icontains')
    data_inicio_de = filters.DateFilter(field_name='data_inicio', lookup_expr='gte')
    data_inicio_ate = filters.DateFilter(field_name='data_inicio', lookup_expr='lte')
    data_fim_de = filters.DateFilter(field_name='data_fim', lookup_expr='gte')
    data_fim_ate = filters.DateFilter(field_name='data_fim', lookup_expr='lte')

    class Meta:
        model = Contrato
        fields = [
            'id_contrato',
            'funcionario',
            'funcionario_nome',
            'tipo_contrato',
            'data_inicio_de',
            'data_inicio_ate',
            'data_fim_de',
            'data_fim_ate',
        ]
