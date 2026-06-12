from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
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
    """Mascara CPF quando contexto nao pode ver dado sensivel."""
    return '***.***.***-**' if value else value


def mask_email(value):
    """Mascara parte local do e-mail quando leitura nao e privilegiada."""
    if not value or '@' not in value:
        return value

    local, domain = value.split('@', 1)
    visible = local[:1] if local else ''
    return f'{visible}***@{domain}'


def mask_phone(value):
    """Mascara telefone quando contexto nao pode ver dado sensivel."""
    return '***********' if value else value


def can_view_candidato_sensitive(serializer, candidato):
    """Indica se contexto pode ver dados pessoais do candidato."""
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
            'user',
            'nome',
            'email',
            'telefone',
            'curriculo',
        ]
        read_only_fields = fields
        depth = 1

    def get_cpf_candidato(self, obj) -> str | None:
        """Retorna CPF real ou mascarado conforme permissao."""
        if can_view_candidato_sensitive(self, obj):
            return obj.cpf_candidato
        return mask_cpf(obj.cpf_candidato)

    def get_email(self, obj) -> str | None:
        """Retorna e-mail real ou mascarado conforme permissao."""
        if can_view_candidato_sensitive(self, obj):
            return obj.email
        return mask_email(obj.email)

    def get_telefone(self, obj) -> str | None:
        """Retorna telefone real ou mascarado conforme permissao."""
        if can_view_candidato_sensitive(self, obj):
            return obj.telefone
        return mask_phone(obj.telefone)

    def get_curriculo(self, obj) -> str | None:
        """Retorna curriculo apenas para contexto autorizado."""
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
            'user',
            'nome',
            'email',
            'telefone',
            'curriculo',
        ]
        read_only_fields = [
            'user',
        ]

    def validate_cpf_candidato(self, value):
        """Bloqueia duplicidade de CPF no cadastro de candidato."""
        if self.instance and str(self.instance.pk) == str(value):
            return value

        if Candidato.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Ja existe candidato com este CPF.')

        return value

    def validate_nome(self, value):
        """Normaliza nome opcional do candidato quando enviado."""
        if value in [None, '']:
            return value
        return normalize_required_text(value, 'nome')

    def validate(self, attrs):
        """Normaliza contato e curriculo do candidato."""
        if 'email' in attrs:
            attrs['email'] = normalize_optional_text(attrs.get('email'))
        if 'telefone' in attrs:
            attrs['telefone'] = normalize_optional_text(attrs.get('telefone'))
        if 'curriculo' in attrs:
            attrs['curriculo'] = normalize_optional_text(attrs.get('curriculo'))

        return attrs


class CandidatoRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
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
    email = serializers.EmailField()
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

    def validate_username(self, value):
        """Normaliza username e bloqueia duplicidade no registro."""
        value = normalize_required_text(value, 'username')
        UserModel = get_user_model()

        if UserModel.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Ja existe usuario com este username.')

        return value

    def validate_cpf_candidato(self, value):
        """Bloqueia registro publico com CPF ja cadastrado."""
        if Candidato.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Ja existe candidato com este CPF.')

        return value

    def validate(self, attrs):
        """Valida e-mail, senha e campos opcionais do registro."""
        UserModel = get_user_model()
        email = normalize_required_text(attrs.get('email'), 'email')

        if UserModel.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({
                'email': 'Ja existe usuario com este e-mail.',
            })

        password_user = UserModel(
            username=attrs.get('username'),
            email=email,
        )
        try:
            password_validation.validate_password(attrs.get('password'), user=password_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc

        attrs['email'] = email
        if 'nome' in attrs:
            attrs['nome'] = normalize_optional_text(attrs.get('nome'))
        if 'telefone' in attrs:
            attrs['telefone'] = normalize_optional_text(attrs.get('telefone'))
        if 'curriculo' in attrs:
            attrs['curriculo'] = normalize_optional_text(attrs.get('curriculo'))

        return attrs

    def create(self, validated_data):
        """Cria usuario Django e candidato em transacao unica."""
        UserModel = get_user_model()
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        email = validated_data.get('email')

        with transaction.atomic():
            user = UserModel.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            return Candidato.objects.create(user=user, **validated_data)


class CandidatoComVagasReadSerializer(serializers.ModelSerializer):
    cpf_candidato = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()
    curriculo = serializers.SerializerMethodField()

    class Meta:
        model = Candidato
        fields = [
            'cpf_candidato',
            'user',
            'nome',
            'email',
            'telefone',
            'curriculo',
            'candidatovaga_set',
        ]
        read_only_fields = fields
        depth = 1

    def get_cpf_candidato(self, obj) -> str | None:
        """Retorna CPF real ou mascarado em leitura com vagas."""
        if can_view_candidato_sensitive(self, obj):
            return obj.cpf_candidato
        return mask_cpf(obj.cpf_candidato)

    def get_email(self, obj) -> str | None:
        """Retorna e-mail real ou mascarado em leitura com vagas."""
        if can_view_candidato_sensitive(self, obj):
            return obj.email
        return mask_email(obj.email)

    def get_telefone(self, obj) -> str | None:
        """Retorna telefone real ou mascarado em leitura com vagas."""
        if can_view_candidato_sensitive(self, obj):
            return obj.telefone
        return mask_phone(obj.telefone)

    def get_curriculo(self, obj) -> str | None:
        """Retorna curriculo apenas para contexto autorizado com vagas."""
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
        """Normaliza titulo opcional da vaga quando enviado."""
        if value in [None, '']:
            return value
        return normalize_required_text(value, 'titulo')

    def validate(self, attrs):
        """Valida data de publicacao e normaliza descricao da vaga."""
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
        """Retorna CPF real ou mascarado do vinculo candidato-vaga."""
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
        """Valida unicidade do vinculo candidato-vaga."""
        if not self.partial and (attrs.get('cpf_candidato') is None or attrs.get('id_vaga') is None):
            raise serializers.ValidationError(
                'Candidato e vaga sao obrigatorios para criar o vinculo.'
            )

        candidato = attrs.get('cpf_candidato') or getattr(self.instance, 'cpf_candidato', None)
        vaga = attrs.get('id_vaga') or getattr(self.instance, 'id_vaga', None)

        if candidato and vaga:
            duplicate_queryset = CandidatoVaga.objects.filter(cpf_candidato=candidato, id_vaga=vaga)
            if self.instance is not None:
                duplicate_queryset = duplicate_queryset.exclude(
                    cpf_candidato_id=getattr(self.instance, 'cpf_candidato_id', None),
                    id_vaga_id=getattr(self.instance, 'id_vaga_id', None),
                )

            if duplicate_queryset.exists():
                raise serializers.ValidationError({
                    'id_vaga': 'Candidato ja inscrito nesta vaga.',
                })

        if 'status_processo' in attrs:
            attrs['status_processo'] = normalize_optional_text(attrs.get('status_processo'))

        return attrs


class CandidaturaCreateSerializer(serializers.Serializer):
    id_vaga = serializers.PrimaryKeyRelatedField(queryset=Vaga.objects.all())

    def validate(self, attrs):
        """Impede candidatura duplicada para a mesma vaga."""
        candidato = self.context['candidato']
        vaga = attrs['id_vaga']

        if CandidatoVaga.objects.filter(cpf_candidato=candidato, id_vaga=vaga).exists():
            raise serializers.ValidationError({
                'id_vaga': 'Candidato ja inscrito nesta vaga.',
            })

        return attrs

    def create(self, validated_data):
        """Cria candidatura com status inicial candidato."""
        return CandidatoVaga.objects.create(
            cpf_candidato=self.context['candidato'],
            id_vaga=validated_data['id_vaga'],
            status_processo='candidatado',
        )


CandidatoSerializer = CandidatoReadSerializer
VagaSerializer = VagaReadSerializer
CandidatoVagaSerializer = CandidatoVagaReadSerializer
