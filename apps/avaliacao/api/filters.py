from django_filters import rest_framework as filters

from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho


class AnaliseComportamentalFilter(filters.FilterSet):
    funcionario = filters.NumberFilter(field_name='fk_id_funcionario')
    funcionario_nome = filters.CharFilter(field_name='fk_id_funcionario__nome', lookup_expr='icontains')
    setor = filters.NumberFilter(field_name='fk_id_funcionario__fk_id_setor')
    data_analise_de = filters.DateFilter(field_name='data_analise', lookup_expr='gte')
    data_analise_ate = filters.DateFilter(field_name='data_analise', lookup_expr='lte')

    class Meta:
        model = AnaliseComportamental
        fields = [
            'id_analise',
            'funcionario',
            'funcionario_nome',
            'setor',
            'data_analise_de',
            'data_analise_ate',
        ]


class AvaliacaoDesempenhoFilter(filters.FilterSet):
    funcionario = filters.NumberFilter(field_name='fk_id_funcionario')
    avaliador = filters.NumberFilter(field_name='fk_id_avaliador')
    funcionario_nome = filters.CharFilter(field_name='fk_id_funcionario__nome', lookup_expr='icontains')
    avaliador_nome = filters.CharFilter(field_name='fk_id_avaliador__nome', lookup_expr='icontains')
    categoria = filters.CharFilter(field_name='categoria', lookup_expr='icontains')
    nota_min = filters.NumberFilter(field_name='nota', lookup_expr='gte')
    nota_max = filters.NumberFilter(field_name='nota', lookup_expr='lte')
    data_avaliacao_de = filters.DateFilter(field_name='data_avaliacao', lookup_expr='gte')
    data_avaliacao_ate = filters.DateFilter(field_name='data_avaliacao', lookup_expr='lte')

    class Meta:
        model = AvaliacaoDesempenho
        fields = [
            'id_avaliacao',
            'funcionario',
            'avaliador',
            'funcionario_nome',
            'avaliador_nome',
            'categoria',
            'nota_min',
            'nota_max',
            'data_avaliacao_de',
            'data_avaliacao_ate',
        ]
