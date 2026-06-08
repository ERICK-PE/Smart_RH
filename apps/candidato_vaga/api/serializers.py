from django.utils import timezone
from rest_framework import serializers

from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga
from apps.validators import (
    cpf_format_validator,
    nome_validators,
    normalize_optional_text,
    normalize_required_text,
    phone_format_validator,
    safe_text_validator,
    status_processo_validator,
)


class CandidatoReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidato
        fields = [
            'cpf_candidato',
            'nome',
            'email',
            'telefone',
            'curriculo',
        ]
        read_only_fields = fields
        depth = 1


class CandidatoWriteSerializer(serializers.ModelSerializer):
    cpf_candidato = serializers.CharField(
        max_length=15,
        validators=[cpf_format_validator],
    )
    nome = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=nome_validators,
    )
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    telefone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[phone_format_validator],
    )

    class Meta:
        model = Candidato
        fields = [
            'cpf_candidato',
            'nome',
            'email',
            'telefone',
            'curriculo',
        ]
        read_only_fields = []

    def validate_nome(self, value):
        if value in [None, '']:
            return value
        return normalize_required_text(value, 'nome')

    def validate(self, attrs):
        if 'email' in attrs:
            attrs['email'] = normalize_optional_text(attrs.get('email'))
        if 'telefone' in attrs:
            attrs['telefone'] = normalize_optional_text(attrs.get('telefone'))
        if 'curriculo' in attrs:
            attrs['curriculo'] = normalize_optional_text(attrs.get('curriculo'))

        return attrs


class CandidatoComVagasReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidato
        fields = [
            'cpf_candidato',
            'nome',
            'email',
            'telefone',
            'curriculo',
            'candidatovaga_set',
        ]
        read_only_fields = fields
        depth = 1


class VagaReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaga
        fields = [
            'id_vaga',
            'titulo',
            'descricao',
            'data_publicacao',
            'fk_id_setor',
        ]
        read_only_fields = fields
        depth = 1


class VagaWriteSerializer(serializers.ModelSerializer):
    titulo = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=nome_validators,
    )

    class Meta:
        model = Vaga
        fields = [
            'id_vaga',
            'titulo',
            'descricao',
            'data_publicacao',
            'fk_id_setor',
        ]
        read_only_fields = [
            'id_vaga',
        ]

    def validate_titulo(self, value):
        if value in [None, '']:
            return value
        return normalize_required_text(value, 'titulo')

    def validate(self, attrs):
        data_publicacao = attrs.get('data_publicacao')

        if data_publicacao and data_publicacao > timezone.localdate():
            raise serializers.ValidationError({
                'data_publicacao': 'Data de publicacao nao pode ser futura.',
            })

        if 'descricao' in attrs:
            attrs['descricao'] = normalize_optional_text(attrs.get('descricao'))

        return attrs


class VagaComCandidatosReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaga
        fields = [
            'id_vaga',
            'titulo',
            'descricao',
            'data_publicacao',
            'fk_id_setor',
            'candidatovaga_set',
        ]
        read_only_fields = fields
        depth = 1


class CandidatoVagaReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidatoVaga
        fields = [
            'cpf_candidato',
            'id_vaga',
            'status_processo',
        ]
        read_only_fields = fields
        depth = 1


class CandidatoVagaWriteSerializer(serializers.ModelSerializer):
    status_processo = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[safe_text_validator, status_processo_validator],
    )

    class Meta:
        model = CandidatoVaga
        fields = [
            'cpf_candidato',
            'id_vaga',
            'status_processo',
        ]
        read_only_fields = []

    def validate(self, attrs):
        if not self.partial and (attrs.get('cpf_candidato') is None or attrs.get('id_vaga') is None):
            raise serializers.ValidationError(
                'Candidato e vaga sao obrigatorios para criar o vinculo.'
            )

        if 'status_processo' in attrs:
            attrs['status_processo'] = normalize_optional_text(attrs.get('status_processo'))

        return attrs


CandidatoSerializer = CandidatoReadSerializer
VagaSerializer = VagaReadSerializer
CandidatoVagaSerializer = CandidatoVagaReadSerializer
