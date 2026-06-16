import logging
from importlib.util import find_spec

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.http import JsonResponse
from django.urls import include, path
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


logger = logging.getLogger(__name__)


def api_root_view(request):
    """Retorna catalogo de descoberta da API publica sob /api/."""
    drf_spectacular_available = bool(find_spec('drf_spectacular'))
    docs = {
        'schema': request.build_absolute_uri('schema/') if drf_spectacular_available else None,
        'swagger': request.build_absolute_uri('docs/') if drf_spectacular_available else None,
        'redoc': request.build_absolute_uri('redoc/') if drf_spectacular_available else None,
    }

    return JsonResponse({
        'name': 'Smart-RH API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'token': request.build_absolute_uri('auth/token/'),
                'refresh': request.build_absolute_uri('auth/token/refresh/'),
            },
            'setor': request.build_absolute_uri('setor/'),
            'funcionario': request.build_absolute_uri('funcionario/'),
            'avaliacao': request.build_absolute_uri('avaliacao/'),
            'candidato': request.build_absolute_uri('candidato/'),
        },
        'documentation': docs,
        'documentation_enabled': drf_spectacular_available,
    })


def _has_group(user, group_names):
    """Verifica pertencimento a grupos esperados sem expor dados sensiveis."""
    user_group_names = user.groups.values_list('name', flat=True)
    return any((group_name or '').lower() in group_names for group_name in user_group_names)


def _has_permission(user, permissions):
    """Verifica permissoes formais usadas pelo frontend para rotas."""
    return any(user.has_perm(permission) for permission in permissions)


def _resolve_profile(user, funcionario_id, candidato_cpf):
    """Resolve perfil principal respeitando a hierarquia de acesso do backend."""
    rh_groups = {'rh', 'recursos_humanos', 'administrador', 'admin'}
    lideranca_groups = {'lideranca', 'gerente', 'coordenador', 'supervisor', 'diretor'}
    rh_permissions = {'funcionario.view_rh_panel', 'funcionario.manage_rh'}
    lideranca_permissions = {'funcionario.view_lideranca', 'funcionario.manage_lideranca'}

    if user.is_staff or user.is_superuser:
        return 'rh_admin'
    if _has_group(user, rh_groups) or _has_permission(user, rh_permissions):
        return 'rh_admin'
    if _has_group(user, lideranca_groups) or _has_permission(user, lideranca_permissions):
        return 'lideranca'
    if funcionario_id is not None:
        return 'funcionario'
    if candidato_cpf is not None:
        return 'candidato'
    return None


def _assert_rh_admin_user(user):
    """Garante que apenas RH/admin gerencie usuarios do sistema."""
    rh_groups = {'rh', 'recursos_humanos', 'administrador', 'admin'}
    rh_permissions = {'funcionario.view_rh_panel', 'funcionario.manage_rh'}
    if user.is_staff or user.is_superuser:
        return
    if _has_group(user, rh_groups) or _has_permission(user, rh_permissions):
        return
    raise PermissionDenied('Acesso permitido apenas para RH ou administrador.')


def _get_user_link(user, related_name):
    """Busca vinculo opcional do usuario sem quebrar quando a tabela nao existe."""
    try:
        return getattr(user, related_name, None)
    except ObjectDoesNotExist:
        return None
    except DatabaseError:
        logger.warning('Tabela de %s indisponivel ao resolver usuario %s.', related_name, user.pk)
        return None


def _serialize_user(user):
    """Monta resposta administrativa de usuario sem expor senha."""
    funcionario = _get_user_link(user, 'funcionario')
    candidato = _get_user_link(user, 'candidato')
    linked_person = funcionario or candidato
    full_name = user.get_full_name().strip()

    return {
        'id': user.pk,
        'username': user.get_username(),
        'nome': getattr(linked_person, 'nome', None) or full_name or user.get_username(),
        'email': getattr(linked_person, 'email', None) or user.email,
        'telefone': getattr(linked_person, 'telefone', None),
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


def _apply_user_payload(user, data):
    """Atualiza dados basicos do usuario e do vinculo pessoal quando existir."""
    funcionario = _get_user_link(user, 'funcionario')
    candidato = _get_user_link(user, 'candidato')
    linked_person = funcionario or candidato

    if 'username' in data:
        username = str(data.get('username') or '').strip()
        if not username:
            return {'username': 'Nome de usuario e obrigatorio.'}
        user.username = username

    if 'nome' in data:
        nome = str(data.get('nome') or '').strip()
        if linked_person is not None:
            linked_person.nome = nome
        else:
            user.first_name = nome
            user.last_name = ''

    if 'email' in data:
        email = str(data.get('email') or '').strip()
        user.email = email
        if linked_person is not None:
            linked_person.email = email

    if 'telefone' in data and linked_person is not None:
        linked_person.telefone = str(data.get('telefone') or '').strip()

    for boolean_field in ['is_active', 'is_staff']:
        if boolean_field in data:
            value = data.get(boolean_field)
            user_value = value if isinstance(value, bool) else str(value).lower() in {'true', '1', 'sim'}
            setattr(user, boolean_field, user_value)

    try:
        with transaction.atomic():
            user.save()
            if linked_person is not None:
                linked_person.save()
    except DatabaseError:
        logger.exception('Erro ao atualizar usuario %s.', user.pk)
        return {'detail': 'Nao foi possivel atualizar o usuario.'}

    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usuarios_view(request):
    """Lista usuarios do sistema para o painel administrativo."""
    _assert_rh_admin_user(request.user)
    UserModel = get_user_model()
    search = (request.query_params.get('search') or '').strip()
    queryset = UserModel.objects.all().order_by('id')

    if search:
        queryset = queryset.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )

    page_number = request.query_params.get('page') or 1
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_number)

    return Response({
        'count': paginator.count,
        'next': page.next_page_number() if page.has_next() else None,
        'previous': page.previous_page_number() if page.has_previous() else None,
        'results': [_serialize_user(user) for user in page.object_list],
    })


@api_view(['GET', 'PATCH', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def usuario_detail_view(request, pk):
    """Consulta, edita ou remove usuario no painel administrativo."""
    _assert_rh_admin_user(request.user)
    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(pk=pk)
    except UserModel.DoesNotExist:
        return Response({'detail': 'Usuario nao encontrado.'}, status=404)

    if request.method == 'GET':
        return Response(_serialize_user(user))

    if request.method in {'PATCH', 'PUT'}:
        errors = _apply_user_payload(user, request.data)
        if errors:
            return Response(errors, status=400)
        return Response(_serialize_user(user))

    if user.pk == request.user.pk:
        return Response({'detail': 'Nao e permitido excluir o proprio usuario autenticado.'}, status=400)

    try:
        with transaction.atomic():
            funcionario = _get_user_link(user, 'funcionario')
            candidato = _get_user_link(user, 'candidato')
            if funcionario is not None:
                funcionario.user = None
                funcionario.save(update_fields=['user'])
            if candidato is not None:
                candidato.user = None
                candidato.save(update_fields=['user'])
            user.delete()
    except DatabaseError:
        logger.exception('Erro ao excluir usuario %s.', user.pk)
        return Response({'detail': 'Nao foi possivel excluir o usuario.'}, status=400)

    return Response(status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_me_view(request):
    """Retorna dados minimos de sessao para o frontend autenticado."""
    user = request.user
    try:
        funcionario = getattr(user, 'funcionario', None)
    except ObjectDoesNotExist:
        funcionario = None
    except DatabaseError:
        logger.warning('Tabela de funcionario indisponivel ao resolver sessao do usuario %s.', user.pk)
        funcionario = None
    try:
        candidato = getattr(user, 'candidato', None)
    except ObjectDoesNotExist:
        candidato = None
    except DatabaseError:
        logger.warning('Tabela de candidato indisponivel ao resolver sessao do usuario %s.', user.pk)
        candidato = None
    funcionario_id = getattr(funcionario, 'pk', None)
    candidato_cpf = getattr(candidato, 'pk', None)
    profile = _resolve_profile(user, funcionario_id, candidato_cpf)
    linked_person = funcionario or candidato
    get_full_name = getattr(user, 'get_full_name', None)
    full_name = get_full_name().strip() if callable(get_full_name) else ''
    nome = getattr(linked_person, 'nome', None) or full_name or user.get_username()
    logger.info('Sessao resolvida para usuario %s com perfil %s.', user.pk, profile)

    return JsonResponse({
        'id': user.pk,
        'username': user.get_username(),
        'nome': nome,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'groups': list(user.groups.values_list('name', flat=True)),
        'permissions': sorted(user.get_all_permissions()),
        'profile': profile,
        'funcionario_id': funcionario_id,
        'candidato_cpf': candidato_cpf,
    })


urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', auth_me_view, name='auth-me'),
    path('auth/usuarios/', usuarios_view, name='auth-usuarios'),
    path('auth/usuarios/<int:pk>/', usuario_detail_view, name='auth-usuario-detail'),
    path('setor/', include('apps.setor.api.urls')),
    path('funcionario/', include('apps.funcionario.api.urls')),
    path('avaliacao/', include('apps.avaliacao.api.urls')),
    path('candidato/', include('apps.candidato_vaga.api.urls')),
]

if find_spec('drf_spectacular'):
    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

    urlpatterns += [
        path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
        path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
        path('redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),
    ]

urlpatterns.append(path('', api_root_view, name='smart-rh-api-root'))
