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


def mask_cpf(value):
    return '***.***.***-**' if value else value


def mask_email(value):
    if not value or '@' not in value:
        return value

    local, domain = value.split('@', 1)
    visible = local[:1] if local else ''
    return f'{visible}***@{domain}'


def mask_phone(value):
    return '***********' if value else value


def can_view_candidato_sensitive(serializer, candidato):
    request = serializer.context.get('request')
    view = serializer.context.get('view')
    user = getattr(request, 'user', None)

    if view and getattr(view, 'user_has_rh_admin_access', None) and view.user_has_rh_admin_access():
        return True
    if user and getattr(user, 'is_authenticated', False):
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True

    if view and getattr(view, 'get_request_candidato_cpf', None):
        cpf_candidato = view.get_request_candidato_cpf(required=False)
        return str(cpf_candidato) == str(getattr(candidato, 'pk', None))

    return False


class CandidatoReadSerializer(serializers.ModelSerializer):
    cpf_candidato = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()
    curriculo = serializers.SerializerMethodField()

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

    def get_cpf_candidato(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.cpf_candidato
        return mask_cpf(obj.cpf_candidato)

    def get_email(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.email
        return mask_email(obj.email)

    def get_telefone(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.telefone
        return mask_phone(obj.telefone)

    def get_curriculo(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.curriculo
        return None


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
    curriculo = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[safe_text_validator],
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

    def validate_cpf_candidato(self, value):
        if self.instance and str(self.instance.pk) == str(value):
            return value

        if Candidato.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Ja existe candidato com este CPF.')

        return value

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
    cpf_candidato = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()
    curriculo = serializers.SerializerMethodField()

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

    def get_cpf_candidato(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.cpf_candidato
        return mask_cpf(obj.cpf_candidato)

    def get_email(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.email
        return mask_email(obj.email)

    def get_telefone(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.telefone
        return mask_phone(obj.telefone)

    def get_curriculo(self, obj) -> str | None:
        if can_view_candidato_sensitive(self, obj):
            return obj.curriculo
        return None


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
    cpf_candidato = serializers.SerializerMethodField()

    class Meta:
        model = CandidatoVaga
        fields = [
            'cpf_candidato',
            'id_vaga',
            'status_processo',
        ]
        read_only_fields = fields
        depth = 1

    def get_cpf_candidato(self, obj) -> str | None:
        candidato = obj.cpf_candidato
        if can_view_candidato_sensitive(self, candidato):
            return candidato.pk
        return mask_cpf(candidato.pk)


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


class CandidaturaCreateSerializer(serializers.Serializer):
    id_vaga = serializers.PrimaryKeyRelatedField(queryset=Vaga.objects.all())

    def validate(self, attrs):
        candidato = self.context['candidato']
        vaga = attrs['id_vaga']

        if CandidatoVaga.objects.filter(cpf_candidato=candidato, id_vaga=vaga).exists():
            raise serializers.ValidationError({
                'id_vaga': 'Candidato ja inscrito nesta vaga.',
            })

        return attrs

    def create(self, validated_data):
        return CandidatoVaga.objects.create(
            cpf_candidato=self.context['candidato'],
            id_vaga=validated_data['id_vaga'],
            status_processo='candidatado',
        )


CandidatoSerializer = CandidatoReadSerializer
VagaSerializer = VagaReadSerializer
CandidatoVagaSerializer = CandidatoVagaReadSerializer
