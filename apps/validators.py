from django.core.validators import MinLengthValidator, RegexValidator
from rest_framework import serializers


nome_min_length_validator = MinLengthValidator(
    3,
    message='Nome deve ter pelo menos 3 caracteres.',
)

safe_text_validator = RegexValidator(
    regex=r'^[^<>]+$',
    message='Campo nao pode conter < ou >.',
)

cpf_format_validator = RegexValidator(
    regex=r'^(\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})$',
    message='CPF deve estar no formato 00000000000 ou 000.000.000-00.',
)

phone_format_validator = RegexValidator(
    regex=r'^[0-9()+\-\s]*$',
    message='Telefone deve conter apenas numeros, espacos, parenteses, + ou -.',
)

status_processo_validator = RegexValidator(
    regex=r'^[A-Za-z0-9 _-]+$',
    message='Status do processo deve conter apenas letras, numeros, espaco, _ ou -.',
)

nome_validators = [
    nome_min_length_validator,
    safe_text_validator,
]


def normalize_required_text(value, field_name):
    if value is None:
        raise serializers.ValidationError(f'{field_name} e obrigatorio.')

    normalized_value = ' '.join(str(value).split())
    if not normalized_value:
        raise serializers.ValidationError(f'{field_name} nao pode ser vazio.')

    return normalized_value


def normalize_optional_text(value):
    if value is None:
        return value

    normalized_value = ' '.join(str(value).split())
    return normalized_value or None
