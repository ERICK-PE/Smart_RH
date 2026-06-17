from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.candidato_vaga.api.serializers import build_case_insensitive_query, get_candidato_username_variants
from apps.candidato_vaga.models import Candidato
from apps.funcionario.models import Funcionario


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
