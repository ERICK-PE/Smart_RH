from rest_framework import serializers

from apps.setor.models import Cargo, Setor
from apps.validators import nome_validators, normalize_optional_text, normalize_required_text


def setor_summary(setor):
    """Retorna dados publicos minimos de setor."""
    if setor is None:
        return None

    return {
        'id_setor': getattr(setor, 'id_setor', None),
        'nome': getattr(setor, 'nome', None),
    }


class SetorReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = [
            'id_setor',
            'nome',
            'descricao',
        ]
        read_only_fields = fields


class SetorWriteSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(validators=nome_validators)

    class Meta:
        model = Setor
        fields = [
            'id_setor',
            'nome',
            'descricao',
        ]
        read_only_fields = [
            'id_setor',
        ]

    def validate_nome(self, value):
        """Normaliza nome obrigatorio de setor."""
        return normalize_required_text(value, 'nome')

    def validate(self, attrs):
        """Valida consistencia entre nome e descricao do setor."""
        nome = attrs.get('nome')
        descricao = normalize_optional_text(attrs.get('descricao')) if 'descricao' in attrs else None

        if nome and descricao and nome.lower() == descricao.lower():
            raise serializers.ValidationError({
                'descricao': 'Descricao nao pode ser igual ao nome.',
            })

        if 'descricao' in attrs:
            attrs['descricao'] = descricao

        return attrs


class SetorComRelacionamentosReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = [
            'id_setor',
            'nome',
            'descricao',
            'cargo_set',
            'funcionario_set',
            'vaga_set',
        ]
        read_only_fields = fields


class CargoReadSerializer(serializers.ModelSerializer):
    fk_id_setor = serializers.SerializerMethodField()

    class Meta:
        model = Cargo
        fields = [
            'id_cargo',
            'nome',
            'descricao',
            'fk_id_setor',
        ]
        read_only_fields = fields

    def get_fk_id_setor(self, obj) -> dict | None:
        """Retorna resumo seguro do setor vinculado."""
        return setor_summary(obj.fk_id_setor)


class CargoWriteSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(validators=nome_validators)

    class Meta:
        model = Cargo
        fields = [
            'id_cargo',
            'nome',
            'descricao',
            'fk_id_setor',
        ]
        read_only_fields = [
            'id_cargo',
        ]

    def validate_nome(self, value):
        """Normaliza nome obrigatorio de cargo."""
        return normalize_required_text(value, 'nome')

    def validate(self, attrs):
        """Valida consistencia entre nome, descricao e setor do cargo."""
        nome = attrs.get('nome')
        descricao = normalize_optional_text(attrs.get('descricao')) if 'descricao' in attrs else None

        if nome and descricao and nome.lower() == descricao.lower():
            raise serializers.ValidationError({
                'descricao': 'Descricao nao pode ser igual ao nome.',
            })

        if not self.instance and not attrs.get('fk_id_setor'):
            raise serializers.ValidationError({
                'fk_id_setor': 'Informe o setor vinculado ao cargo.',
            })

        if 'descricao' in attrs:
            attrs['descricao'] = descricao

        return attrs


class CargoComRelacionamentosReadSerializer(serializers.ModelSerializer):
    fk_id_setor = serializers.SerializerMethodField()

    class Meta:
        model = Cargo
        fields = [
            'id_cargo',
            'nome',
            'descricao',
            'fk_id_setor',
            'funcionario_set',
            'planocarreira_set',
        ]
        read_only_fields = fields

    def get_fk_id_setor(self, obj) -> dict | None:
        """Retorna resumo seguro do setor vinculado."""
        return setor_summary(obj.fk_id_setor)


SetorSerializer = SetorReadSerializer
CargoSerializer = CargoReadSerializer
