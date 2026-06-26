from django.db.models import Q
from django_filters import rest_framework as filters

from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga


class CandidatoFilter(filters.FilterSet):
    nome = filters.CharFilter(field_name='nome', lookup_expr='icontains')
    possui_curriculo = filters.BooleanFilter(method='filter_possui_curriculo')

    class Meta:
        model = Candidato
        fields = ['cpf_candidato', 'nome', 'possui_curriculo']

    def filter_possui_curriculo(self, queryset, name, value):
        """Filtra candidatos com ou sem curriculo preenchido."""
        empty_curriculo = Q(curriculo__isnull=True) | Q(curriculo='')
        if value:
            return queryset.exclude(empty_curriculo)
        return queryset.filter(empty_curriculo)


class VagaFilter(filters.FilterSet):
    titulo = filters.CharFilter(field_name='titulo', lookup_expr='icontains')
    status = filters.ChoiceFilter(field_name='status', choices=Vaga.STATUS_CHOICES)
    setor = filters.NumberFilter(field_name='fk_id_setor')
    setor_nome = filters.CharFilter(field_name='fk_id_setor__nome', lookup_expr='icontains')
    texto = filters.CharFilter(method='filter_texto')
    data_publicacao_de = filters.DateFilter(field_name='data_publicacao', lookup_expr='gte')
    data_publicacao_ate = filters.DateFilter(field_name='data_publicacao', lookup_expr='lte')
    com_candidaturas = filters.BooleanFilter(method='filter_com_candidaturas')

    class Meta:
        model = Vaga
        fields = [
            'id_vaga',
            'titulo',
            'status',
            'setor',
            'setor_nome',
            'texto',
            'data_publicacao_de',
            'data_publicacao_ate',
            'com_candidaturas',
        ]

    def filter_texto(self, queryset, name, value):
        """Busca texto em titulo ou descricao da vaga."""
        return queryset.filter(Q(titulo__icontains=value) | Q(descricao__icontains=value))

    def filter_com_candidaturas(self, queryset, name, value):
        """Filtra vagas com ou sem candidaturas vinculadas."""
        return queryset.filter(candidatovaga__isnull=not value).distinct()


class CandidatoVagaFilter(filters.FilterSet):
    candidato = filters.CharFilter(field_name='cpf_candidato')
    vaga = filters.NumberFilter(field_name='id_vaga')
    status_processo = filters.CharFilter(field_name='status_processo', lookup_expr='icontains')
    triagem_automatica_aprovada = filters.BooleanFilter(field_name='triagem_automatica_aprovada')
    candidato_nome = filters.CharFilter(field_name='cpf_candidato__nome', lookup_expr='icontains')
    vaga_titulo = filters.CharFilter(field_name='id_vaga__titulo', lookup_expr='icontains')

    class Meta:
        model = CandidatoVaga
        fields = [
            'candidato',
            'vaga',
            'status_processo',
            'triagem_automatica_aprovada',
            'candidato_nome',
            'vaga_titulo',
        ]
