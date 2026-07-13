from django.db import transaction
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from rest_framework import serializers

from apps.avaliacao.models import (
    AnaliseComportamental,
    AnaliseComportamentalEnvio,
    AnaliseComportamentalResposta,
    AvaliacaoDesempenho,
)
from apps.funcionario.api.serializers import (
    can_view_funcionario_sensitive,
    funcionario_summary,
)
from apps.funcionario.models import Funcionario
from apps.setor.models import Setor
from apps.validators import normalize_optional_text


ANALISE_COMPORTAMENTAL_PERGUNTAS = [
    {
        'id': 'sentimento',
        'titulo': 'Termômetro de sentimento',
        'pergunta': 'Como você se sente no seu trabalho atualmente?',
        'tipo': 'select',
        'opcoes': ['Muito Infeliz', 'Infeliz', 'Neutro', 'Feliz', 'Muito Feliz'],
    },
    {
        'id': 'sentimento_observacao',
        'titulo': 'Termômetro de sentimento',
        'pergunta': 'Alguma observação?',
        'tipo': 'textarea',
        'obrigatoria': False,
    },
    {
        'id': 'desenvolvimento_profissional',
        'titulo': 'Desenvolvimento profissional',
        'pergunta': 'Você se sente apoiado profissionalmente na empresa?',
        'tipo': 'select',
        'opcoes': ['Sempre', 'Na maioria das vezes', 'Às vezes', 'Raramente', 'Nunca'],
    },
    {
        'id': 'reconhecimento',
        'titulo': 'Senso de reconhecimento',
        'pergunta': 'Como você se sente em relação ao reconhecimento pelo seu trabalho?',
        'tipo': 'select',
        'opcoes': ['Muito valorizado', 'Valorizado', 'Neutro', 'Pouco valorizado', 'Não valorizado'],
    },
    {
        'id': 'ambiente_fisico',
        'titulo': 'Ambiente de trabalho',
        'pergunta': 'Como você avaliaria seu ambiente físico de trabalho?',
        'tipo': 'select',
        'opcoes': ['1', '2', '3', '4', '5'],
    },
    {
        'id': 'clima_geral',
        'titulo': 'Ambiente de trabalho',
        'pergunta': 'Como você avaliaria o clima geral do seu ambiente de trabalho?',
        'tipo': 'select',
        'opcoes': ['1', '2', '3', '4', '5'],
    },
    {
        'id': 'lideranca_empresa',
        'titulo': 'Liderança da empresa',
        'pergunta': 'Qual sua percepção sobre o estilo de liderança da empresa?',
        'tipo': 'select',
        'opcoes': ['Inspirador', 'Apoiador', 'Neutra', 'Crítico', 'Autoritário'],
    },
    {
        'id': 'relacao_colegas',
        'titulo': 'Relação com colegas',
        'pergunta': 'Como você avalia sua relação com os colegas e equipe?',
        'tipo': 'select',
        'opcoes': ['1', '2', '3', '4', '5'],
    },
]


def can_view_avaliacao_sensitive(serializer, avaliacao):
    """Indica se contexto pode ver comentario ou resultado sensivel."""
    if can_view_funcionario_sensitive(serializer, avaliacao.fk_id_funcionario):
        return True

    view = serializer.context.get('view')
    if view and getattr(view, 'get_request_funcionario_id', None):
        funcionario_id = view.get_request_funcionario_id(required=False)
        return str(funcionario_id) == str(getattr(avaliacao, 'fk_id_avaliador_id', None))

    return False


class AnaliseComportamentalReadSerializer(serializers.ModelSerializer):
    fk_id_funcionario = serializers.SerializerMethodField()
    resultado = serializers.SerializerMethodField()

    class Meta:
        model = AnaliseComportamental
        fields = [
            'id_analise',
            'fk_id_funcionario',
            'resultado',
            'data_analise',
        ]
        read_only_fields = fields

    def get_fk_id_funcionario(self, obj) -> dict | None:
        """Retorna resumo seguro do funcionario avaliado."""
        return funcionario_summary(obj.fk_id_funcionario)

    def get_resultado(self, obj) -> str | None:
        """Retorna resultado apenas para contexto autorizado."""
        if can_view_funcionario_sensitive(self, obj.fk_id_funcionario):
            return obj.resultado
        return None


class AnaliseComportamentalWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnaliseComportamental
        fields = [
            'id_analise',
            'fk_id_funcionario',
            'resultado',
            'data_analise',
        ]
        read_only_fields = [
            'id_analise',
        ]

    def validate(self, attrs):
        """Valida data da analise e normaliza resultado."""
        data_analise = attrs.get('data_analise')

        if data_analise and data_analise > timezone.localdate():
            raise serializers.ValidationError({
                'data_analise': 'Data da analise nao pode ser futura.',
            })

        if 'resultado' in attrs:
            attrs['resultado'] = normalize_optional_text(attrs.get('resultado'))

        return attrs


class AnaliseComportamentalEnvioReadSerializer(serializers.ModelSerializer):
    fk_id_funcionario = serializers.SerializerMethodField()
    fk_id_setor = serializers.SerializerMethodField()
    total_respostas = serializers.SerializerMethodField()
    total_pendentes = serializers.SerializerMethodField()

    class Meta:
        model = AnaliseComportamentalEnvio
        fields = [
            'id_envio',
            'fk_id_funcionario',
            'fk_id_setor',
            'titulo',
            'perguntas',
            'criado_em',
            'total_respostas',
            'total_pendentes',
        ]
        read_only_fields = fields

    def get_fk_id_funcionario(self, obj) -> dict | None:
        if not obj.fk_id_funcionario_id:
            return None
        return funcionario_summary(obj.fk_id_funcionario)

    def get_fk_id_setor(self, obj) -> dict | None:
        if not obj.fk_id_setor_id:
            return None
        return {
            'id_setor': obj.fk_id_setor_id,
            'nome': getattr(obj.fk_id_setor, 'nome', None),
        }

    def get_total_respostas(self, obj) -> int:
        return obj.respostas.count()

    def get_total_pendentes(self, obj) -> int:
        return obj.respostas.filter(status=AnaliseComportamentalResposta.STATUS_PENDENTE).count()


class AnaliseComportamentalEnvioCreateSerializer(serializers.ModelSerializer):
    fk_id_funcionario = serializers.PrimaryKeyRelatedField(
        queryset=Funcionario.objects.all(),
        required=False,
        allow_null=True,
    )
    fk_id_setor = serializers.PrimaryKeyRelatedField(
        queryset=Setor.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AnaliseComportamentalEnvio
        fields = [
            'id_envio',
            'fk_id_funcionario',
            'fk_id_setor',
        ]
        read_only_fields = ['id_envio']

    def validate(self, attrs):
        funcionario = attrs.get('fk_id_funcionario')
        setor = attrs.get('fk_id_setor')

        if bool(funcionario) == bool(setor):
            raise serializers.ValidationError(
                'Informe funcionario ou setor, mas nao ambos.'
            )

        if setor:
            total = Funcionario.objects.filter(
                fk_id_setor=setor,
                status=Funcionario.STATUS_ATIVO,
            ).count()
            if total == 0:
                raise serializers.ValidationError({
                    'fk_id_setor': 'Setor sem funcionarios ativos para envio.',
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        funcionario = validated_data.get('fk_id_funcionario')
        setor = validated_data.get('fk_id_setor')

        envio = AnaliseComportamentalEnvio.objects.create(
            fk_id_funcionario=funcionario,
            fk_id_setor=setor,
            titulo='Analise comportamental',
            perguntas=ANALISE_COMPORTAMENTAL_PERGUNTAS,
            criado_por=user if getattr(user, 'is_authenticated', False) else None,
        )

        if funcionario:
            funcionarios = [funcionario]
        else:
            funcionarios = list(
                Funcionario.objects.filter(
                    fk_id_setor=setor,
                    status=Funcionario.STATUS_ATIVO,
                )
            )

        AnaliseComportamentalResposta.objects.bulk_create(
            [
                AnaliseComportamentalResposta(
                    fk_id_envio=envio,
                    fk_id_funcionario=funcionario_alvo,
                    respostas={},
                    status=AnaliseComportamentalResposta.STATUS_PENDENTE,
                )
                for funcionario_alvo in funcionarios
            ],
            ignore_conflicts=True,
        )

        return envio


class AnaliseComportamentalRespostaReadSerializer(serializers.ModelSerializer):
    titulo = serializers.CharField(source='fk_id_envio.titulo', read_only=True)
    perguntas = serializers.JSONField(source='fk_id_envio.perguntas', read_only=True)
    criado_em = serializers.DateTimeField(source='fk_id_envio.criado_em', read_only=True)

    class Meta:
        model = AnaliseComportamentalResposta
        fields = [
            'id_resposta',
            'titulo',
            'perguntas',
            'respostas',
            'status',
            'criado_em',
            'respondido_em',
        ]
        read_only_fields = fields


class AnaliseComportamentalRespostaSubmitSerializer(serializers.Serializer):
    respostas = serializers.DictField(child=serializers.CharField(allow_blank=True))

    def validate_respostas(self, respostas):
        question_by_id = {
            question['id']: question
            for question in ANALISE_COMPORTAMENTAL_PERGUNTAS
        }

        for question_id, question in question_by_id.items():
            if question.get('obrigatoria') is False:
                continue

            value = normalize_optional_text(respostas.get(question_id))
            if not value:
                raise serializers.ValidationError(
                    f'Resposta obrigatoria ausente: {question_id}.'
                )

            options = question.get('opcoes')
            if options and value not in options:
                raise serializers.ValidationError(
                    f'Resposta invalida para {question_id}.'
                )

        cleaned = {}
        for question_id, value in respostas.items():
            if question_id not in question_by_id:
                raise serializers.ValidationError(
                    f'Pergunta desconhecida: {question_id}.'
                )
            cleaned[question_id] = normalize_optional_text(value)

        return cleaned

    def save(self, **kwargs):
        resposta = self.context['resposta']
        respostas = self.validated_data['respostas']

        resposta.respondido_em = timezone.now()
        try:
            from apps.avaliacao.services.analise_comportamental_ia import (
                fallback_behavioral_analysis_report,
                generate_behavioral_analysis_report,
            )

            resultado_ia = generate_behavioral_analysis_report(resposta, respostas)
        except ValueError as exc:
            resultado_ia = fallback_behavioral_analysis_report(str(exc))
        except Exception:
            resultado_ia = fallback_behavioral_analysis_report('Falha ao consultar OpenAI.')

        resposta.respostas = respostas
        resposta.status = AnaliseComportamentalResposta.STATUS_RESPONDIDO
        with transaction.atomic():
            resposta.save(update_fields=['respostas', 'status', 'respondido_em'])
            AnaliseComportamental.objects.create(
                fk_id_funcionario=resposta.fk_id_funcionario,
                resultado=resultado_ia,
                data_analise=timezone.localdate(),
            )

        return resposta


class AvaliacaoDesempenhoReadSerializer(serializers.ModelSerializer):
    fk_id_funcionario = serializers.SerializerMethodField()
    fk_id_avaliador = serializers.SerializerMethodField()
    comentario = serializers.SerializerMethodField()

    class Meta:
        model = AvaliacaoDesempenho
        fields = [
            'id_avaliacao',
            'fk_id_funcionario',
            'fk_id_avaliador',
            'categoria',
            'nota',
            'comentario',
            'data_avaliacao',
        ]
        read_only_fields = fields

    def get_fk_id_funcionario(self, obj) -> dict | None:
        """Retorna resumo seguro do funcionario avaliado."""
        return funcionario_summary(obj.fk_id_funcionario)

    def get_fk_id_avaliador(self, obj) -> dict | None:
        """Retorna resumo seguro do avaliador."""
        return funcionario_summary(obj.fk_id_avaliador)

    def get_comentario(self, obj) -> str | None:
        """Retorna comentario apenas para contexto autorizado."""
        if can_view_avaliacao_sensitive(self, obj):
            return obj.comentario
        return None


class AvaliacaoDesempenhoWriteSerializer(serializers.ModelSerializer):
    nota = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
    )

    class Meta:
        model = AvaliacaoDesempenho
        fields = [
            'id_avaliacao',
            'fk_id_funcionario',
            'fk_id_avaliador',
            'categoria',
            'nota',
            'comentario',
            'data_avaliacao',
        ]
        read_only_fields = [
            'id_avaliacao',
        ]

    def validate(self, attrs):
        """Valida avaliacao, nota, data e bloqueia se autoavaliacao."""
        funcionario = attrs.get('fk_id_funcionario')
        avaliador = attrs.get('fk_id_avaliador')
        data_avaliacao = attrs.get('data_avaliacao')

        if funcionario and avaliador and funcionario == avaliador:
            raise serializers.ValidationError({
                'fk_id_avaliador': 'Avaliador nao pode ser o proprio funcionario avaliado.',
            })

        if data_avaliacao and data_avaliacao > timezone.localdate():
            raise serializers.ValidationError({
                'data_avaliacao': 'Data da avaliacao nao pode ser futura.',
            })

        if 'comentario' in attrs:
            attrs['comentario'] = normalize_optional_text(attrs.get('comentario'))

        return attrs


AnaliseComportamentalSerializer = AnaliseComportamentalReadSerializer
AvaliacaoDesempenhoSerializer = AvaliacaoDesempenhoReadSerializer
