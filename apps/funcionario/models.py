from pathlib import Path
import re

from django.conf import settings
from django.db import models


def sanitize_document_upload_path(folder, filename):
    """Monta caminho de documento preservando nome base sanitizado."""
    file_path = Path(filename or 'documento')
    extension = file_path.suffix.lower()
    stem = file_path.stem.strip() or 'documento'
    safe_stem = re.sub(r'[^A-Za-z0-9_.-]+', '_', stem).strip('._-') or 'documento'
    return f'{folder}/{safe_stem}{extension}'


def contrato_upload_path(instance, filename):
    """Monta caminho logico do arquivo de contrato."""
    return sanitize_document_upload_path('contratos', filename)


def folha_pagamento_upload_path(instance, filename):
    """Monta caminho logico do arquivo de folha de pagamento."""
    return sanitize_document_upload_path('folhas_pagamento', filename)


class Funcionario(models.Model):
    STATUS_ATIVO = 'ativo'
    STATUS_INATIVO = 'inativo'
    STATUS_CHOICES = [
        (STATUS_ATIVO, 'Ativo'),
        (STATUS_INATIVO, 'Inativo'),
    ]

    id_funcionario = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        models.DO_NOTHING,
        db_column='user_id',
        related_name='funcionario',
        blank=True,
        null=True,
    )
    nome = models.CharField(max_length=150)
    cpf = models.CharField(unique=True, max_length=14)
    email = models.CharField(unique=True, max_length=150, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_admissao = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ATIVO)
    fk_id_setor = models.ForeignKey('setor.Setor', 
                                    models.DO_NOTHING, 
                                    db_column='fk_id_setor')
    fk_id_cargo = models.ForeignKey('setor.Cargo', 
                                    models.DO_NOTHING, 
                                    db_column='fk_id_cargo')

    def __str__(self):
        """Retorna nome do funcionario sem expor dados sensiveis."""
        return self.nome

    class Meta:
        managed = False
        db_table = 'funcionario'
        permissions = [
            ('view_lideranca', 'Pode acessar recursos de leitura da lideranca'),
            ('manage_lideranca', 'Pode gerenciar recursos da lideranca'),
            ('view_rh_panel', 'Pode acessar paineis de RH'),
            ('manage_rh', 'Pode gerenciar recursos de RH'),
        ]


class PlanoCarreira(models.Model):
    id_plano = models.AutoField(primary_key=True)
    fk_id_cargo = models.ForeignKey('setor.Cargo', 
                                    models.DO_NOTHING, 
                                    db_column='fk_id_cargo')
    fk_id_criador = models.ForeignKey(
        Funcionario,
        models.DO_NOTHING,
        db_column='fk_id_criador',
        related_name='planos_criados',
        blank=True,
        null=True,
    )
    descricao = models.TextField(blank=True, null=True)
    requisitos = models.TextField(blank=True, null=True)

    def __str__(self):
        """Retorna identificador legivel do plano de carreira."""
        return f'Plano de carreira {self.id_plano}'

    class Meta:
        managed = False
        db_table = 'plano_carreira'


class Contrato(models.Model):
    id_contrato = models.AutoField(primary_key=True)
    fk_id_funcionario = models.ForeignKey(Funcionario, models.DO_NOTHING, db_column='fk_id_funcionario')
    tipo_contrato = models.CharField(max_length=50, blank=True, null=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    arquivo = models.FileField(
        upload_to=contrato_upload_path,
        max_length=255,
        blank=True,
        null=True,
    )

    def __str__(self):
        """Retorna identificador legivel do contrato sem salario."""
        return f'Contrato {self.id_contrato}'

    class Meta:
        managed = False
        db_table = 'contrato'


class FolhaPagamento(models.Model):
    id_folha = models.AutoField(primary_key=True)
    fk_id_funcionario = models.ForeignKey(Funcionario, models.DO_NOTHING, db_column='fk_id_funcionario')
    competencia = models.CharField(max_length=20, blank=True, null=True)
    arquivo = models.FileField(upload_to=folha_pagamento_upload_path, max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Retorna identificador legivel da folha sem expor arquivo."""
        return f'Folha de pagamento {self.id_folha}'

    class Meta:
        db_table = 'folha_pagamento'


def funcionario_agente_documento_upload_path(instance, filename):
    """Monta caminho logico em imp_doc preservando nome base enviado."""
    basename = (filename or '').replace('\\', '/').split('/')[-1].strip() or 'documento'
    return f'imp_doc/{basename}'


class FuncionarioAgenteDocumento(models.Model):
    id_documento = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=150)
    arquivo = models.FileField(upload_to=funcionario_agente_documento_upload_path, max_length=255)
    conteudo_extraido = models.TextField()
    ativo = models.BooleanField(default=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        db_column='id_usuario',
        blank=True,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Retorna titulo do documento sem expor conteudo interno."""
        return self.titulo

    class Meta:
        db_table = 'agente_documento'
