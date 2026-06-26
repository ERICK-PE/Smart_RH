import re
from pathlib import Path

from django.conf import settings
from django.db import models


def candidato_curriculo_upload_path(instance, filename):
    """Monta caminho do curriculo usando nome original sanitizado."""
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    stem = file_path.stem.strip() or 'curriculo'
    safe_stem = re.sub(r'[^A-Za-z0-9_.-]+', '_', stem).strip('._-') or 'curriculo'
    return f'curriculos/{safe_stem}{extension}'


class Candidato(models.Model):
    cpf_candidato = models.CharField(primary_key=True, max_length=15)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        models.DO_NOTHING,
        db_column='user_id',
        related_name='candidato',
        blank=True,
        null=True,
    )
    nome = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    curriculo = models.FileField(
        upload_to=candidato_curriculo_upload_path,
        max_length=255,
        blank=True,
        null=True,
    )

    def __str__(self):
        """Retorna nome ou identificador do candidato sem contato."""
        return self.nome or f'Candidato {self.cpf_candidato}'

    class Meta:
        managed = False
        db_table = 'candidato'


class Vaga(models.Model):
    STATUS_ABERTA = 'aberta'
    STATUS_ANDAMENTO = 'andamento'
    STATUS_FECHADA = 'fechada'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_ABERTA, 'Aberta'),
        (STATUS_ANDAMENTO, 'Andamento'),
        (STATUS_FECHADA, 'Fechada'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    id_vaga = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=150, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ABERTA)
    fk_id_setor = models.ForeignKey('setor.Setor',
                                     models.DO_NOTHING, 
                                     db_column='fk_id_setor', 
                                     blank=True, null=True)

    def __str__(self):
        """Retorna titulo ou identificador da vaga."""
        return self.titulo or f'Vaga {self.id_vaga}'

    class Meta:
        managed = False
        db_table = 'vaga'


class CandidatoVaga(models.Model):
    pk = models.CompositePrimaryKey('cpf_candidato', 'id_vaga')
    cpf_candidato = models.ForeignKey(Candidato, models.DO_NOTHING, db_column='cpf_candidato')
    id_vaga = models.ForeignKey(Vaga, models.DO_NOTHING, db_column='id_vaga')
    status_processo = models.CharField(max_length=50, blank=True, null=True)
    triagem_automatica_aprovada = models.BooleanField(blank=True, null=True)
    triagem_automatica_motivo = models.TextField(blank=True, null=True)
    triagem_automatica_palavras_chave = models.TextField(blank=True, null=True)

    def __str__(self):
        """Retorna chave do vinculo candidato-vaga."""
        return f'Candidato {self.cpf_candidato_id} - Vaga {self.id_vaga_id}'

    class Meta:
        managed = False
        db_table = 'candidato_vaga'
