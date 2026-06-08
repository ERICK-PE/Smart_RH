from django.core.validators import MinValueValidator
from django.utils import timezone
from rest_framework import serializers

from apps.funcionario.models import Contrato, Funcionario, PlanoCarreira
from apps.validators import (
    cpf_format_validator,
    nome_validators,
    normalize_optional_text,
    normalize_required_text,
    phone_format_validator,
)


class FuncionarioReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'fk_id_setor',
            'fk_id_cargo',
        ]
        read_only_fields = fields
        depth = 1


class FuncionarioWriteSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(validators=nome_validators)
    cpf = serializers.CharField(validators=[cpf_format_validator])
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    telefone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[phone_format_validator],
    )

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'fk_id_setor',
            'fk_id_cargo',
        ]
        read_only_fields = [
            'id_funcionario',
        ]

    def validate_nome(self, value):
        return normalize_required_text(value, 'nome')

    def validate(self, attrs):
        data_admissao = attrs.get('data_admissao')

        if data_admissao and data_admissao > timezone.localdate():
            raise serializers.ValidationError({
                'data_admissao': 'Data de admissao nao pode ser futura.',
            })

        if 'telefone' in attrs:
            attrs['telefone'] = normalize_optional_text(attrs.get('telefone'))
        if 'email' in attrs:
            attrs['email'] = normalize_optional_text(attrs.get('email'))

        return attrs


class FuncionarioComRelacionamentosReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'fk_id_setor',
            'fk_id_cargo',
            'contrato_set',
            'analisecomportamental_set',
            'avaliacaodesempenho_set',
            'avaliacaodesempenho_fk_id_avaliador_set',
        ]
        read_only_fields = fields
        depth = 1


class PlanoCarreiraReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanoCarreira
        fields = [
            'id_plano',
            'fk_id_cargo',
            'descricao',
            'requisitos',
        ]
        read_only_fields = fields
        depth = 1


class PlanoCarreiraWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanoCarreira
        fields = [
            'id_plano',
            'fk_id_cargo',
            'descricao',
            'requisitos',
        ]
        read_only_fields = [
            'id_plano',
        ]

    def validate(self, attrs):
        descricao = normalize_optional_text(attrs.get('descricao')) if 'descricao' in attrs else None
        requisitos = normalize_optional_text(attrs.get('requisitos')) if 'requisitos' in attrs else None

        if ('descricao' in attrs or 'requisitos' in attrs or not self.partial) and not descricao and not requisitos:
            raise serializers.ValidationError({
                'requisitos': 'Informe descricao ou requisitos do plano de carreira.',
            })

        if 'descricao' in attrs:
            attrs['descricao'] = descricao
        if 'requisitos' in attrs:
            attrs['requisitos'] = requisitos

        return attrs


class ContratoReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contrato
        fields = [
            'id_contrato',
            'fk_id_funcionario',
            'tipo_contrato',
            'salario',
            'data_inicio',
            'data_fim',
        ]
        read_only_fields = fields
        depth = 1


class ContratoWriteSerializer(serializers.ModelSerializer):
    salario = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        model = Contrato
        fields = [
            'id_contrato',
            'fk_id_funcionario',
            'tipo_contrato',
            'salario',
            'data_inicio',
            'data_fim',
        ]
        read_only_fields = [
            'id_contrato',
        ]

    def validate(self, attrs):
        data_inicio = attrs.get('data_inicio')
        data_fim = attrs.get('data_fim')

        if data_fim and data_inicio and data_fim < data_inicio:
            raise serializers.ValidationError({
                'data_fim': 'Data fim nao pode ser anterior a data inicio.',
            })

        return attrs


FuncionarioSerializer = FuncionarioReadSerializer
PlanoCarreiraSerializer = PlanoCarreiraReadSerializer
ContratoSerializer = ContratoReadSerializer
