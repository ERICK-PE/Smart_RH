import unicodedata

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.candidato_vaga.api.serializers import build_case_insensitive_query, get_candidato_username_variants
from apps.candidato_vaga.models import Candidato
from apps.funcionario.models import Funcionario


RH_ADMIN_GROUP_NAMES = {
    'rh',
    'recursos_humanos',
    'administrador',
    'admin',
}
RH_ADMIN_PERMISSIONS = {
    'funcionario.view_rh_panel',
    'funcionario.manage_rh',
}
LIDERANCA_GROUP_NAMES = {
    'lideranca',
    'gerente',
    'coordenador',
    'supervisor',
    'diretor',
}
LIDERANCA_PERMISSIONS = {
    'funcionario.view_lideranca',
    'funcionario.manage_lideranca',
}
LIDERANCA_CARGO_NAMES = {
    'lider',
    'lideranca',
    'gerente',
    'coordenador',
    'supervisor',
    'diretor',
}


def normalize_label(value):
    normalized = unicodedata.normalize('NFKD', value or '')
    without_accents = ''.join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.strip().lower()


def get_user_groups(user):
    groups_manager = getattr(user, 'groups', None)
    values_list = getattr(groups_manager, 'values_list', None)
    if not callable(values_list):
        return []
    return list(values_list('name', flat=True))


def get_user_permissions(user):
    get_all_permissions = getattr(user, 'get_all_permissions', None)
    if not callable(get_all_permissions):
        return []
    return sorted(get_all_permissions())


def get_related_or_none(user, related_name):
    try:
        return getattr(user, related_name, None)
    except ObjectDoesNotExist:
        return None


def is_rh_admin_user(user, groups, permissions):
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True
    normalized_groups = {normalize_label(group) for group in groups}
    return bool(
        normalized_groups.intersection(RH_ADMIN_GROUP_NAMES)
        or set(permissions).intersection(RH_ADMIN_PERMISSIONS)
    )


def is_lideranca_user(funcionario, groups, permissions):
    normalized_groups = {normalize_label(group) for group in groups}
    cargo_nome = normalize_label(getattr(getattr(funcionario, 'fk_id_cargo', None), 'nome', ''))
    return bool(
        normalized_groups.intersection(LIDERANCA_GROUP_NAMES)
        or set(permissions).intersection(LIDERANCA_PERMISSIONS)
        or cargo_nome in LIDERANCA_CARGO_NAMES
    )


def build_session_user(user):
    """Monta contrato de sessao para o frontend sem expor credenciais."""
    groups = get_user_groups(user)
    permissions = get_user_permissions(user)
    get_username = getattr(user, 'get_username', None)
    username = get_username() if callable(get_username) else getattr(user, 'username', '')
    get_full_name = getattr(user, 'get_full_name', None)
    full_name = get_full_name() if callable(get_full_name) else ''
    funcionario = get_related_or_none(user, 'funcionario')
    candidato = get_related_or_none(user, 'candidato')
    funcionario_id = getattr(funcionario, 'pk', None)
    candidato_cpf = getattr(candidato, 'pk', None)
    is_rh_admin = is_rh_admin_user(user, groups, permissions)
    is_lideranca = bool(funcionario_id and is_lideranca_user(funcionario, groups, permissions))
    is_funcionario = bool(funcionario_id)
    is_candidato = bool(candidato_cpf)

    if is_rh_admin:
        profile = 'rh_admin'
    elif is_lideranca:
        profile = 'lideranca'
    elif is_funcionario:
        profile = 'funcionario'
    elif is_candidato:
        profile = 'candidato'
    else:
        profile = None

    return {
        'id': user.pk,
        'username': username,
        'email': getattr(user, 'email', '') or '',
        'nome': (
            getattr(funcionario, 'nome', None)
            or getattr(candidato, 'nome', None)
            or full_name
            or username
        ),
        'is_staff': bool(getattr(user, 'is_staff', False)),
        'is_superuser': bool(getattr(user, 'is_superuser', False)),
        'groups': groups,
        'permissions': permissions,
        'profile': profile,
        'funcionario_id': funcionario_id,
        'candidato_cpf': candidato_cpf,
        'is_rh_admin': is_rh_admin,
        'is_funcionario': is_funcionario,
        'is_lideranca': is_lideranca,
        'is_candidato': is_candidato,
    }


class SmartRHTokenObtainPairSerializer(TokenObtainPairSerializer):
    profile = serializers.ChoiceField(
        choices=['candidato', 'funcionario', 'rh', 'admin'],
        required=False,
        write_only=True,
    )

    def validate(self, attrs):
        profile = attrs.pop('profile', None)
        username = attrs.get(self.username_field)

        if profile and username:
            attrs[self.username_field] = self.get_profile_auth_username(profile, username)

        return super().validate(attrs)

    def get_profile_auth_username(self, profile, username):
        if profile == 'candidato':
            candidato = (
                Candidato.objects
                .select_related('user')
                .filter(build_case_insensitive_query('user__username', get_candidato_username_variants(username)))
                .first()
            )
            if candidato and candidato.user_id:
                return candidato.user.get_username()

        if profile in ['funcionario', 'rh', 'admin']:
            funcionario = (
                Funcionario.objects
                .select_related('user')
                .filter(user__username__iexact=username)
                .first()
            )
            if funcionario and funcionario.user_id:
                return funcionario.user.get_username()

        return username


class SmartRHTokenObtainPairView(TokenObtainPairView):
    serializer_class = SmartRHTokenObtainPairSerializer


class SmartRHMeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField(allow_blank=True)
    nome = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    groups = serializers.ListField(child=serializers.CharField())
    permissions = serializers.ListField(child=serializers.CharField())
    profile = serializers.ChoiceField(
        choices=['rh_admin', 'lideranca', 'funcionario', 'candidato'],
        allow_null=True,
    )
    funcionario_id = serializers.IntegerField(allow_null=True)
    candidato_cpf = serializers.CharField(allow_null=True)
    is_rh_admin = serializers.BooleanField()
    is_funcionario = serializers.BooleanField()
    is_lideranca = serializers.BooleanField()
    is_candidato = serializers.BooleanField()


class SmartRHMeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SmartRHMeSerializer

    def get(self, request):
        """Retorna sessao autenticada usada pelo frontend."""
        return Response(self.get_serializer(build_session_user(request.user)).data)
