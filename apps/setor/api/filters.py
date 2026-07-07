from django_filters import rest_framework as filters

from apps.setor.models import Cargo, Setor


class SetorFilter(filters.FilterSet):
    nome = filters.CharFilter(field_name='nome', lookup_expr='icontains')
    descricao = filters.CharFilter(field_name='descricao', lookup_expr='icontains')
    possui_funcionarios = filters.BooleanFilter(method='filter_possui_funcionarios')
    possui_vagas = filters.BooleanFilter(method='filter_possui_vagas')

    class Meta:
        model = Setor
        fields = ['id_setor', 'nome', 'descricao', 'possui_funcionarios', 'possui_vagas']

    def filter_possui_funcionarios(self, queryset, name, value):
        """Filtra setores com ou sem funcionarios vinculados."""
        return queryset.filter(funcionario__isnull=not value).distinct()

    def filter_possui_vagas(self, queryset, name, value):
        """Filtra setores com ou sem vagas vinculadas."""
        return queryset.filter(vaga__isnull=not value).distinct()


class CargoFilter(filters.FilterSet):
    nome = filters.CharFilter(field_name='nome', lookup_expr='icontains')
    descricao = filters.CharFilter(field_name='descricao', lookup_expr='icontains')
    setor = filters.NumberFilter(field_name='fk_id_setor')
    setor_nome = filters.CharFilter(field_name='fk_id_setor__nome', lookup_expr='icontains')
    possui_funcionarios = filters.BooleanFilter(method='filter_possui_funcionarios')
    possui_planos_carreira = filters.BooleanFilter(method='filter_possui_planos_carreira')

    class Meta:
        model = Cargo
        fields = [
            'id_cargo',
            'nome',
            'descricao',
            'setor',
            'setor_nome',
            'possui_funcionarios',
            'possui_planos_carreira',
        ]

    def filter_possui_funcionarios(self, queryset, name, value):
        """Filtra cargos com ou sem funcionarios vinculados."""
        return queryset.filter(funcionario__isnull=not value).distinct()

    def filter_possui_planos_carreira(self, queryset, name, value):
        """Filtra cargos com ou sem planos de carreira vinculados."""
        return queryset.filter(planocarreira__isnull=not value).distinct()
