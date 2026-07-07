from django.db.models import Avg, Count, Q
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api_mixins import RHAdminAccessMixin
from apps.avaliacao.models import AvaliacaoDesempenho
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga
from apps.funcionario.models import Funcionario


def grouped_counts(queryset, value_field, count_field, empty_label='sem_informacao'):
    """Retorna contagens agregadas em lista legivel para graficos."""
    return [
        {
            'label': item[value_field] or empty_label,
            'total': item['total'],
        }
        for item in queryset.values(value_field).annotate(total=Count(count_field)).order_by(value_field)
    ]


class SmartRHDashboardRHView(RHAdminAccessMixin, APIView):
    """Dashboard agregado para o perfil RH/admin."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        self.assert_rh_admin_access()

        funcionarios = Funcionario.objects.select_related('fk_id_setor', 'fk_id_cargo').all()
        funcionarios_ativos = funcionarios.filter(status=Funcionario.STATUS_ATIVO)
        funcionarios_com_contrato = funcionarios.filter(contrato__isnull=False).distinct()
        funcionarios_sem_contrato = funcionarios.exclude(pk__in=funcionarios_com_contrato.values('pk'))
        funcionarios_com_plano = funcionarios.filter(fk_id_cargo__planocarreira__isnull=False).distinct()
        funcionarios_sem_plano = funcionarios.exclude(pk__in=funcionarios_com_plano.values('pk'))
        funcionarios_avaliados = funcionarios.filter(avaliacaodesempenho__isnull=False).distinct()
        avaliacoes_pendentes = funcionarios_ativos.exclude(pk__in=funcionarios_avaliados.values('pk')).count()

        total_funcionarios = funcionarios.count()
        total_funcionarios_ativos = funcionarios_ativos.count()
        total_funcionarios_sem_contrato = funcionarios_sem_contrato.count()
        total_funcionarios_com_plano = funcionarios_com_plano.count()
        percentual_funcionarios_com_plano = (
            round((total_funcionarios_com_plano / total_funcionarios) * 100, 2)
            if total_funcionarios
            else 0
        )

        vagas = Vaga.objects.all()
        candidaturas = CandidatoVaga.objects.all()
        media_nota = AvaliacaoDesempenho.objects.aggregate(media=Avg('nota'))['media']
        contratados = candidaturas.filter(
            Q(status_processo__iexact='contratado')
            | Q(status_processo__iexact='contratada')
            | Q(status_processo__iexact='admitido')
            | Q(status_processo__iexact='admitida')
        ).count()

        candidatos_por_vaga = [
            {
                'label': item['id_vaga__titulo'] or f"Vaga {item['id_vaga']}",
                'total': item['total'],
            }
            for item in (
                candidaturas
                .values('id_vaga', 'id_vaga__titulo')
                .annotate(total=Count('cpf_candidato'))
                .order_by('-total', 'id_vaga__titulo')
            )
        ]

        return Response({
            'resumo': {
                'funcionarios_ativos': total_funcionarios_ativos,
                'funcionarios_sem_contrato': total_funcionarios_sem_contrato,
                'funcionarios_com_plano_percentual': percentual_funcionarios_com_plano,
                'total_vagas': vagas.count(),
            },
            'empresa': {
                'funcionarios_por_setor': grouped_counts(
                    funcionarios,
                    'fk_id_setor__nome',
                    'id_funcionario',
                    'sem_setor',
                ),
                'funcionarios_por_cargo': grouped_counts(
                    funcionarios,
                    'fk_id_cargo__nome',
                    'id_funcionario',
                    'sem_cargo',
                ),
                'funcionarios_por_status': grouped_counts(
                    funcionarios,
                    'status',
                    'id_funcionario',
                    'sem_status',
                ),
            },
            'avaliacoes': {
                'planos_carreira_cobertura': {
                    'com_plano': total_funcionarios_com_plano,
                    'sem_plano': funcionarios_sem_plano.count(),
                    'percentual_com_plano': percentual_funcionarios_com_plano,
                },
                'media_avaliacoes': float(media_nota) if media_nota is not None else None,
                'avaliacoes_pendentes': avaliacoes_pendentes,
            },
            'recrutamento': {
                'funil': {
                    'vagas': vagas.count(),
                    'candidatos': Candidato.objects.count(),
                    'candidaturas': candidaturas.count(),
                    'contratados': contratados,
                },
                'candidatos_por_vaga': candidatos_por_vaga,
                'vagas_por_status': grouped_counts(
                    vagas,
                    'status',
                    'id_vaga',
                    'sem_status',
                ),
            },
        })
