from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied
from rest_framework.response import Response


class ResumoActionMixin:
    @action(detail=False, methods=['get'], url_path='resumo')
    def resumo(self, request):
        """Retorna total simples do queryset atual."""
        return Response({
            'total': self.get_queryset().count(),
        })

    def paginated_serializer_response(self, queryset, serializer_class, **serializer_kwargs):
        """Serializa lista manual mantendo paginacao padrao do DRF."""
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
        """Confirma acesso global nativo do Django para staff ou superuser."""
        user = self.request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False))
        )

    def user_has_global_access(self):
        """Indica se usuario pode acessar dados administrativos globais."""
        return self.user_is_staff_or_superuser()

    def user_in_rh_admin_group(self, user):
        """Verifica se usuario pertence a grupo reconhecido como RH/admin."""
        if not getattr(user, 'pk', None):
            return False

        group_names = user.groups.values_list('name', flat=True)
        return any((group_name or '').lower() in self.rh_admin_group_names for group_name in group_names)

    def user_has_rh_admin_permission(self, user):
        """Verifica permissoes formais que liberam painel RH/admin."""
        has_perm = getattr(user, 'has_perm', None)
        if not callable(has_perm):
            return False

        return any(has_perm(permission) for permission in self.rh_admin_permissions)

    def user_has_rh_admin_access(self):
        """Centraliza regra de autorizacao para perfil RH/admin."""
        user = self.request.user
        if self.user_is_staff_or_superuser():
            return True
        if not user or not user.is_authenticated:
            return False

        return self.user_in_rh_admin_group(user) or self.user_has_rh_admin_permission(user)

    def assert_rh_admin_access(self):
        """Bloqueia requisicao quando usuario nao tem perfil RH/admin."""
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
        """Aplica autorizacao RH/admin antes de acoes de escrita."""
        super().initial(request, *args, **kwargs)
        if getattr(self, 'action', None) in self.rh_admin_write_actions:
            self.assert_rh_admin_access()

    def get_serializer_class(self):
        """Usa serializer de escrita nas acoes mutaveis do ViewSet."""
        if (
            self.write_serializer_class
            and getattr(self, 'action', None) in self.rh_admin_write_actions
        ):
            return self.write_serializer_class

        return super().get_serializer_class()


class RHAdminOnlyModelViewSetMixin(RHAdminModelViewSetMixin):
    def initial(self, request, *args, **kwargs):
        """Aplica autorizacao RH/admin para leitura e escrita."""
        super().initial(request, *args, **kwargs)
        self.assert_rh_admin_access()


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
        """Busca model Funcionario sem import direto para evitar ciclo."""
        return apps.get_model('funcionario', 'Funcionario')

    def user_has_global_access(self):
        """Reaproveita regra RH/admin como acesso global para funcionario."""
        return self.user_has_rh_admin_access()

    def get_request_funcionario_id(self, required=True):
        """Resolve funcionario do usuario autenticado por vinculo formal."""
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
        """Carrega funcionario autenticado com setor e cargo relacionados."""
        funcionario_id = self.get_request_funcionario_id(required=required)
        if funcionario_id is None:
            return None

        funcionario = (
            self.get_funcionario_model()
            .objects
            .select_related('fk_id_setor', 'fk_id_cargo', 'fk_id_cargo__fk_id_setor')
            .filter(pk=funcionario_id)
            .first()
        )

        if funcionario is None and required:
            raise PermissionDenied('Funcionario autenticado nao encontrado.')

        return funcionario

    def assert_can_access_funcionario(self, funcionario_id):
        """Garante que funcionario comum acesse apenas o proprio registro."""
        if self.user_has_global_access():
            return

        request_funcionario_id = self.get_request_funcionario_id()
        if str(request_funcionario_id) != str(funcionario_id):
            raise PermissionDenied('Funcionario comum so pode acessar os proprios dados.')

    def get_funcionario_comum_object(self):
        """Retorna objeto de detalhe apos validar escopo do funcionario."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        funcionario_id = self.kwargs.get(lookup_url_kwarg)
        self.assert_can_access_funcionario(funcionario_id)
        return self.get_object()

    def user_has_lideranca_access(self):
        """Verifica acesso de lideranca por grupo, permissao ou RH/admin."""
        if self.user_has_global_access():
            return True

        user = self.request.user
        if not user or not user.is_authenticated:
            return False

        return self.user_in_lideranca_group(user) or self.user_has_lideranca_permission(user)

    def user_in_lideranca_group(self, user):
        """Verifica se usuario esta em grupo reconhecido como lideranca."""
        if not getattr(user, 'pk', None):
            return False

        group_names = user.groups.values_list('name', flat=True)
        return any((group_name or '').lower() in self.lideranca_group_names for group_name in group_names)

    def user_has_lideranca_permission(self, user):
        """Verifica permissoes formais de acesso de lideranca."""
        has_perm = getattr(user, 'has_perm', None)
        if not callable(has_perm):
            return False

        return any(has_perm(permission) for permission in self.lideranca_permissions)

    def user_has_manage_lideranca_permission(self):
        """Confirma permissao especial para gerenciar avaliacoes de lideranca."""
        user = self.request.user
        has_perm = getattr(user, 'has_perm', None)
        return bool(callable(has_perm) and has_perm('funcionario.manage_lideranca'))

    def assert_can_edit_lideranca_avaliacao(self, avaliacao):
        """Bloqueia lideranca editando avaliacao criada por outro avaliador."""
        if self.user_has_global_access() or self.user_has_manage_lideranca_permission():
            return

        request_funcionario_id = self.get_request_funcionario_id()
        if str(avaliacao.fk_id_avaliador_id) != str(request_funcionario_id):
            raise PermissionDenied(
                'Lideranca so pode editar avaliacao criada por ela mesma sem permissao manage_lideranca.'
            )

    def assert_can_edit_lideranca_plano(self, plano):
        """Bloqueia lideranca editando plano de carreira criado por outro lider."""
        if self.user_has_global_access() or self.user_has_manage_lideranca_permission():
            return

        request_funcionario_id = self.get_request_funcionario_id()
        if str(getattr(plano, 'fk_id_criador_id', None)) != str(request_funcionario_id):
            raise PermissionDenied(
                'Lideranca so pode editar plano de carreira criado por ela mesma sem permissao manage_lideranca.'
            )

    def assert_lideranca_access(self):
        """Bloqueia requisicao quando usuario nao tem perfil de lideranca."""
        if not self.user_has_lideranca_access():
            raise PermissionDenied('Acesso permitido apenas para lideranca.')

    def get_funcionario_setor_lideranca(self, funcionario_id):
        """Carrega funcionario e valida escopo do setor da lideranca."""
        try:
            funcionario = (
                self.get_funcionario_model()
                .objects
                .select_related('fk_id_setor', 'fk_id_cargo', 'fk_id_cargo__fk_id_setor')
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
