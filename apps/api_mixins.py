from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied
from rest_framework.response import Response


class ResumoActionMixin:
    @action(detail=False, methods=['get'], url_path='resumo')
    def resumo(self, request):
        return Response({
            'total': self.get_queryset().count(),
        })

    def paginated_serializer_response(self, queryset, serializer_class, **serializer_kwargs):
        serializer_kwargs.setdefault('context', self.get_serializer_context())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = serializer_class(page, many=True, **serializer_kwargs)
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True, **serializer_kwargs)
        return Response(serializer.data)


class RHAdminAccessMixin:
    rh_admin_group_names = {
        'rh',
        'recursos_humanos',
        'administrador',
        'admin',
    }
    rh_admin_permissions = {
        'funcionario.view_rh_panel',
        'funcionario.manage_rh',
    }

    def user_is_staff_or_superuser(self):
        user = self.request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False))
        )

    def user_has_global_access(self):
        return self.user_is_staff_or_superuser()

    def user_in_rh_admin_group(self, user):
        if not getattr(user, 'pk', None):
            return False

        group_names = user.groups.values_list('name', flat=True)
        return any((group_name or '').lower() in self.rh_admin_group_names for group_name in group_names)

    def user_has_rh_admin_permission(self, user):
        has_perm = getattr(user, 'has_perm', None)
        if not callable(has_perm):
            return False

        return any(has_perm(permission) for permission in self.rh_admin_permissions)

    def user_has_rh_admin_access(self):
        user = self.request.user
        if self.user_is_staff_or_superuser():
            return True
        if not user or not user.is_authenticated:
            return False

        return self.user_in_rh_admin_group(user) or self.user_has_rh_admin_permission(user)

    def assert_rh_admin_access(self):
        if not self.user_has_rh_admin_access():
            raise PermissionDenied('Acesso permitido apenas para RH ou administrador.')


class RHAdminModelViewSetMixin(RHAdminAccessMixin):
    write_serializer_class = None
    rh_admin_write_actions = {
        'create',
        'update',
        'partial_update',
        'destroy',
    }

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if getattr(self, 'action', None) in self.rh_admin_write_actions:
            self.assert_rh_admin_access()

    def get_serializer_class(self):
        if (
            self.write_serializer_class
            and getattr(self, 'action', None) in self.rh_admin_write_actions
        ):
            return self.write_serializer_class

        return super().get_serializer_class()


class FuncionarioComumAccessMixin(RHAdminAccessMixin):
    lideranca_group_names = {
        'lideranca',
        'gerente',
        'coordenador',
        'supervisor',
        'diretor',
    }
    lideranca_permissions = {
        'funcionario.view_lideranca',
        'funcionario.manage_lideranca',
    }

    def get_funcionario_model(self):
        return apps.get_model('funcionario', 'Funcionario')

    def user_has_global_access(self):
        return self.user_has_rh_admin_access()

    def get_request_funcionario_id(self, required=True):
        user = self.request.user

        if not user or not user.is_authenticated:
            if required:
                raise NotAuthenticated('Autenticacao obrigatoria.')
            return None

        funcionario_id = getattr(user, 'funcionario_id', None)
        if funcionario_id is None:
            try:
                funcionario = getattr(user, 'funcionario', None)
            except ObjectDoesNotExist:
                funcionario = None
            funcionario_id = getattr(funcionario, 'pk', None)

        if funcionario_id is None and required:
            raise PermissionDenied('Usuario sem vinculo com funcionario.')

        return funcionario_id

    def get_request_funcionario(self, required=True):
        funcionario_id = self.get_request_funcionario_id(required=required)
        if funcionario_id is None:
            return None

        funcionario = (
            self.get_funcionario_model()
            .objects
            .select_related('fk_id_setor', 'fk_id_cargo')
            .filter(pk=funcionario_id)
            .first()
        )

        if funcionario is None and required:
            raise PermissionDenied('Funcionario autenticado nao encontrado.')

        return funcionario

    def assert_can_access_funcionario(self, funcionario_id):
        if self.user_has_global_access():
            return

        request_funcionario_id = self.get_request_funcionario_id()
        if str(request_funcionario_id) != str(funcionario_id):
            raise PermissionDenied('Funcionario comum so pode acessar os proprios dados.')

    def get_funcionario_comum_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        funcionario_id = self.kwargs.get(lookup_url_kwarg)
        self.assert_can_access_funcionario(funcionario_id)
        return self.get_object()

    def user_has_lideranca_access(self):
        if self.user_has_global_access():
            return True

        user = self.request.user
        if not user or not user.is_authenticated:
            return False

        return self.user_in_lideranca_group(user) or self.user_has_lideranca_permission(user)

    def user_in_lideranca_group(self, user):
        if not getattr(user, 'pk', None):
            return False

        group_names = user.groups.values_list('name', flat=True)
        return any((group_name or '').lower() in self.lideranca_group_names for group_name in group_names)

    def user_has_lideranca_permission(self, user):
        has_perm = getattr(user, 'has_perm', None)
        if not callable(has_perm):
            return False

        return any(has_perm(permission) for permission in self.lideranca_permissions)

    def user_has_manage_lideranca_permission(self):
        user = self.request.user
        has_perm = getattr(user, 'has_perm', None)
        return bool(callable(has_perm) and has_perm('funcionario.manage_lideranca'))

    def assert_can_edit_lideranca_avaliacao(self, avaliacao):
        if self.user_has_global_access() or self.user_has_manage_lideranca_permission():
            return

        request_funcionario_id = self.get_request_funcionario_id()
        if str(avaliacao.fk_id_avaliador_id) != str(request_funcionario_id):
            raise PermissionDenied(
                'Lideranca so pode editar avaliacao criada por ela mesma sem permissao manage_lideranca.'
            )

    def assert_lideranca_access(self):
        if not self.user_has_lideranca_access():
            raise PermissionDenied('Acesso permitido apenas para lideranca.')

    def get_funcionario_setor_lideranca(self, funcionario_id):
        try:
            funcionario = (
                self.get_funcionario_model()
                .objects
                .select_related('fk_id_setor', 'fk_id_cargo')
                .get(pk=funcionario_id)
            )
        except self.get_funcionario_model().DoesNotExist as exc:
            raise NotFound('Funcionario nao encontrado.') from exc

        if self.user_has_global_access():
            return funcionario

        self.assert_lideranca_access()
        lider = self.get_request_funcionario()

        if lider.fk_id_setor_id != funcionario.fk_id_setor_id:
            raise PermissionDenied('Lideranca so pode acessar funcionarios do proprio setor.')

        return funcionario
