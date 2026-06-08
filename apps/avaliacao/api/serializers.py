from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from rest_framework import serializers

from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho
from apps.validators import normalize_optional_text


class AnaliseComportamentalReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnaliseComportamental
        fields = [
            'id_analise',
            'fk_id_funcionario',
            'resultado',
            'data_analise',
        ]
        read_only_fields = fields
        depth = 1


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
        data_analise = attrs.get('data_analise')

        if data_analise and data_analise > timezone.localdate():
            raise serializers.ValidationError({
                'data_analise': 'Data da analise nao pode ser futura.',
            })

        if 'resultado' in attrs:
            attrs['resultado'] = normalize_optional_text(attrs.get('resultado'))

        return attrs


class AvaliacaoDesempenhoReadSerializer(serializers.ModelSerializer):
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
        depth = 1


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
