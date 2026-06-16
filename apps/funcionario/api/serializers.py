from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from rest_framework import serializers

from apps.funcionario.models import Contrato, Funcionario, PlanoCarreira
from apps.setor.models import Cargo
from apps.validators import (
    cpf_format_validator,
    nome_validators,
    normalize_optional_text,
    normalize_required_text,
    phone_format_validator,
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


def can_view_funcionario_sensitive(serializer, funcionario):
    """Indica se contexto pode ver dados pessoais do funcionario."""
    request = serializer.context.get('request')
    view = serializer.context.get('view')
    user = getattr(request, 'user', None)

    if view and getattr(view, 'user_has_rh_admin_access', None) and view.user_has_rh_admin_access():
        return True
    if user and getattr(user, 'is_authenticated', False):
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True

    if view and getattr(view, 'get_request_funcionario_id', None):
        funcionario_id = view.get_request_funcionario_id(required=False)
        return str(funcionario_id) == str(getattr(funcionario, 'pk', None))

    return False


class FuncionarioReadSerializer(serializers.ModelSerializer):
    cpf = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    user_access = serializers.SerializerMethodField()

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'user_access',
            'username',
            'is_staff',
            'is_active',
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'status',
            'fk_id_setor',
            'fk_id_cargo',
        ]
        read_only_fields = fields
        depth = 1

    def get_cpf(self, obj) -> str | None:
        """Retorna CPF real ou mascarado conforme permissao."""
        if can_view_funcionario_sensitive(self, obj):
            return obj.cpf
        return mask_cpf(obj.cpf)

    def get_email(self, obj) -> str | None:
        """Retorna e-mail real ou mascarado conforme permissao."""
        if can_view_funcionario_sensitive(self, obj):
            return obj.email
        return mask_email(obj.email)

    def get_telefone(self, obj) -> str | None:
        """Retorna telefone real ou mascarado conforme permissao."""
        if can_view_funcionario_sensitive(self, obj):
            return obj.telefone
        return mask_phone(obj.telefone)

    def get_user_access(self, obj) -> dict | None:
        """Retorna dados seguros do usuario vinculado, nunca senha."""
        if not can_view_funcionario_sensitive(self, obj):
            return None

        user = getattr(obj, 'user', None)
        if user is None:
            return None

        return {
            'id': user.pk,
            'username': user.get_username(),
            'email': user.email,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'last_login': user.last_login,
        }

    def get_username(self, obj) -> str | None:
        """Retorna username vinculado quando o contexto pode ver dados sensiveis."""
        user_access = self.get_user_access(obj)
        return user_access.get('username') if user_access else None

    def get_is_staff(self, obj) -> bool | None:
        """Retorna flag administrativa do usuario vinculado."""
        user_access = self.get_user_access(obj)
        return user_access.get('is_staff') if user_access else None

    def get_is_active(self, obj) -> bool | None:
        """Retorna status de acesso do usuario vinculado."""
        user_access = self.get_user_access(obj)
        return user_access.get('is_active') if user_access else None


class FuncionarioWriteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True, write_only=True)
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True, trim_whitespace=False)
    is_staff = serializers.BooleanField(required=False, allow_null=True, write_only=True)
    nome = serializers.CharField(validators=nome_validators)
    cpf = serializers.CharField(validators=[cpf_format_validator])
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    telefone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[phone_format_validator],
    )
    status = serializers.CharField(required=False)
    fk_id_setor = serializers.PrimaryKeyRelatedField(read_only=True)
    fk_id_cargo = serializers.PrimaryKeyRelatedField(queryset=Cargo.objects.select_related('fk_id_setor').all())

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'username',
            'password',
            'is_staff',
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'status',
            'fk_id_setor',
            'fk_id_cargo',
        ]
        read_only_fields = [
            'id_funcionario',
        ]

    def validate_nome(self, value):
        """Normaliza nome obrigatorio do funcionario."""
        return normalize_required_text(value, 'nome')

    def validate_status(self, value):
        """Valida status permitido para funcionario."""
        value = normalize_required_text(value, 'status').lower()
        valid_statuses = {choice[0] for choice in Funcionario.STATUS_CHOICES}

        if value not in valid_statuses:
            raise serializers.ValidationError('Status deve ser ativo ou inativo.')

        return value

    def validate(self, attrs):
        """Valida dados funcionais e credenciais integradas ao usuario."""
        data_admissao = attrs.get('data_admissao')
        UserModel = get_user_model()

        if data_admissao and data_admissao > timezone.localdate():
            raise serializers.ValidationError({
                'data_admissao': 'Data de admissao nao pode ser futura.',
            })

        if 'telefone' in attrs:
            attrs['telefone'] = normalize_optional_text(attrs.get('telefone'))
        if 'email' in attrs:
            attrs['email'] = normalize_optional_text(attrs.get('email'))

        username = normalize_optional_text(attrs.pop('username', None)) if 'username' in attrs else None
        password = attrs.pop('password', None) if 'password' in attrs else None
        is_staff = attrs.pop('is_staff', None) if 'is_staff' in attrs else None
        email = attrs.get('email') if 'email' in attrs else getattr(self.instance, 'email', None)
        linked_user = getattr(self.instance, 'user', None) if self.instance is not None else None

        if self.instance is None:
            if not username:
                raise serializers.ValidationError({'username': 'Informe o usuario de acesso.'})
            if not password:
                raise serializers.ValidationError({'password': 'Informe a senha inicial do usuario.'})
        elif linked_user is None and (username or password or is_staff is not None):
            if not username:
                raise serializers.ValidationError({'username': 'Informe o usuario de acesso.'})
            if not password:
                raise serializers.ValidationError({'password': 'Informe a senha inicial do usuario.'})

        if username:
            existing_user = UserModel.objects.filter(username__iexact=username)
            if linked_user is not None:
                existing_user = existing_user.exclude(pk=linked_user.pk)
            if existing_user.exists():
                raise serializers.ValidationError({'username': 'Ja existe usuario com este username.'})

        if email:
            existing_email = UserModel.objects.filter(email__iexact=email)
            if linked_user is not None:
                existing_email = existing_email.exclude(pk=linked_user.pk)
            if existing_email.exists():
                raise serializers.ValidationError({'email': 'Ja existe usuario com este e-mail.'})

        if password:
            password_user = linked_user or UserModel(username=username or '', email=email or '')
            try:
                password_validation.validate_password(password, user=password_user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'password': list(exc.messages)}) from exc

        attrs['_user_payload'] = {
            'username': username,
            'password': password,
            'is_staff': is_staff,
        }

        cargo = attrs.get('fk_id_cargo') or getattr(self.instance, 'fk_id_cargo', None)
        if cargo is None:
            raise serializers.ValidationError({
                'fk_id_cargo': 'Informe o cargo do funcionario.',
            })

        setor = getattr(cargo, 'fk_id_setor', None)
        if setor is None:
            raise serializers.ValidationError({
                'fk_id_cargo': 'O cargo selecionado nao possui setor vinculado.',
            })
        attrs['fk_id_setor'] = setor

        return attrs

    def _sync_user(self, funcionario, user_payload):
        """Cria ou atualiza usuario Django a partir do funcionario."""
        UserModel = get_user_model()
        user = funcionario.user
        username = user_payload.get('username')
        password = user_payload.get('password')
        is_staff = user_payload.get('is_staff')

        if user is None:
            username = username or self._default_username(funcionario)
            user = UserModel(username=username, email=funcionario.email or '')

        if username:
            user.username = username

        user.email = funcionario.email or ''
        user.first_name = funcionario.nome
        user.last_name = ''
        user.is_active = funcionario.status != Funcionario.STATUS_INATIVO

        if is_staff is not None:
            user.is_staff = bool(is_staff)
        if password:
            user.set_password(password)
        elif user.pk is None:
            user.set_unusable_password()

        user.save()

        if funcionario.user_id != user.pk:
            funcionario.user = user
            funcionario.save(update_fields=['user'])

        return user

    def _default_username(self, funcionario):
        """Gera username unico para funcionario legado sem usuario."""
        UserModel = get_user_model()
        base = (funcionario.email or funcionario.cpf or f'funcionario{funcionario.pk}').split('@')[0]
        base = ''.join(char for char in base.lower() if char.isalnum() or char in ['.', '_', '-']) or f'funcionario{funcionario.pk}'
        username = base
        suffix = 1

        while UserModel.objects.filter(username__iexact=username).exists():
            suffix += 1
            username = f'{base}{suffix}'

        return username

    def create(self, validated_data):
        """Cria funcionario e usuario de acesso na mesma transacao."""
        user_payload = validated_data.pop('_user_payload', {})
        with transaction.atomic():
            funcionario = super().create(validated_data)
            self._sync_user(funcionario, user_payload)
            return funcionario

    def update(self, instance, validated_data):
        """Atualiza funcionario e sincroniza usuario vinculado."""
        user_payload = validated_data.pop('_user_payload', {})
        with transaction.atomic():
            funcionario = super().update(instance, validated_data)
            self._sync_user(funcionario, user_payload)
            return funcionario


class FuncionarioComRelacionamentosReadSerializer(serializers.ModelSerializer):
    cpf = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    user_access = serializers.SerializerMethodField()

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'user_access',
            'username',
            'is_staff',
            'is_active',
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'status',
            'fk_id_setor',
            'fk_id_cargo',
            'contrato_set',
            'analisecomportamental_set',
            'avaliacaodesempenho_set',
            'avaliacaodesempenho_fk_id_avaliador_set',
        ]
        read_only_fields = fields
        depth = 1

    def get_cpf(self, obj) -> str | None:
        """Retorna CPF real ou mascarado em leitura com relacionamentos."""
        if can_view_funcionario_sensitive(self, obj):
            return obj.cpf
        return mask_cpf(obj.cpf)

    def get_email(self, obj) -> str | None:
        """Retorna e-mail real ou mascarado em leitura com relacionamentos."""
        if can_view_funcionario_sensitive(self, obj):
            return obj.email
        return mask_email(obj.email)

    def get_telefone(self, obj) -> str | None:
        """Retorna telefone real ou mascarado em leitura com relacionamentos."""
        if can_view_funcionario_sensitive(self, obj):
            return obj.telefone
        return mask_phone(obj.telefone)

    def get_user_access(self, obj) -> dict | None:
        """Reaproveita serializacao segura do usuario vinculado."""
        return FuncionarioReadSerializer(context=self.context).get_user_access(obj)

    def get_username(self, obj) -> str | None:
        """Reaproveita username seguro do usuario vinculado."""
        return FuncionarioReadSerializer(context=self.context).get_username(obj)

    def get_is_staff(self, obj) -> bool | None:
        """Reaproveita flag administrativa do usuario vinculado."""
        return FuncionarioReadSerializer(context=self.context).get_is_staff(obj)

    def get_is_active(self, obj) -> bool | None:
        """Reaproveita status de acesso do usuario vinculado."""
        return FuncionarioReadSerializer(context=self.context).get_is_active(obj)


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
        """Exige conteudo minimo do plano de carreira."""
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
    salario = serializers.SerializerMethodField()

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

    def get_salario(self, obj) -> Decimal | None:
        """Retorna salario apenas para RH/admin ou proprio funcionario."""
        request = self.context.get('request')
        view = self.context.get('view')
        user = getattr(request, 'user', None)

        if view and getattr(view, 'user_has_rh_admin_access', None) and view.user_has_rh_admin_access():
            return obj.salario
        if user and getattr(user, 'is_authenticated', False):
            if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
                return obj.salario
        if view and getattr(view, 'get_request_funcionario_id', None):
            funcionario_id = view.get_request_funcionario_id(required=False)
            if str(funcionario_id) == str(obj.fk_id_funcionario_id):
                return obj.salario

        return None


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
        """Valida intervalo de vigencia do contrato."""
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
