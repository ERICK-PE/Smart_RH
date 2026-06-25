from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from rest_framework import serializers

from apps.funcionario.models import Contrato, Funcionario, FuncionarioAgenteDocumento, PlanoCarreira
from apps.funcionario.services.agente_documentos import (
    extract_text_from_document_file,
    save_important_document_upload,
    validate_document_file,
)
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

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'user',
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
    status = serializers.CharField(required=False)

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'user',
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
        """Valida data de admissao e normaliza contato."""
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
    cpf = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'user',
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


class FuncionarioAgenteDocumentoReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuncionarioAgenteDocumento
        fields = [
            'id_documento',
            'titulo',
            'arquivo',
            'ativo',
            'criado_por',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = fields


class FuncionarioAgenteDocumentoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuncionarioAgenteDocumento
        fields = [
            'id_documento',
            'titulo',
            'arquivo',
            'ativo',
        ]
        read_only_fields = [
            'id_documento',
        ]

    def validate_titulo(self, value):
        """Normaliza titulo do documento RH."""
        return normalize_required_text(value, 'titulo')

    def validate_arquivo(self, value):
        """Aceita somente documento RH em PDF, DOC ou DOCX."""
        try:
            validate_document_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        return value

    def validate(self, attrs):
        """Extrai texto do arquivo quando documento e enviado."""
        arquivo = attrs.get('arquivo')
        if arquivo is not None:
            try:
                attrs['conteudo_extraido'] = extract_text_from_document_file(arquivo)
            except ValueError as exc:
                raise serializers.ValidationError({'arquivo': str(exc)}) from exc

        return attrs

    def create(self, validated_data):
        """Salva upload fisico em imp_doc e persiste somente caminho relativo."""
        arquivo = validated_data.pop('arquivo', None)
        if arquivo is not None:
            validated_data['arquivo'] = save_important_document_upload(arquivo)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Atualiza documento mantendo upload fisico em imp_doc."""
        arquivo = validated_data.pop('arquivo', None)
        if arquivo is not None:
            validated_data['arquivo'] = save_important_document_upload(arquivo)
        return super().update(instance, validated_data)


class FuncionarioAgentePerguntaSerializer(serializers.Serializer):
    pergunta = serializers.CharField(max_length=500)

    def validate_pergunta(self, value):
        """Normaliza pergunta do funcionario."""
        pergunta = normalize_required_text(value, 'pergunta')
        if len(pergunta) < 5:
            raise serializers.ValidationError('Pergunta deve ter pelo menos 5 caracteres.')
        return pergunta


FuncionarioSerializer = FuncionarioReadSerializer
PlanoCarreiraSerializer = PlanoCarreiraReadSerializer
ContratoSerializer = ContratoReadSerializer
FuncionarioAgenteDocumentoSerializer = FuncionarioAgenteDocumentoReadSerializer
