from django.db import models


class Setor(models.Model):
    id_setor = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        """Retorna nome do setor para admin e logs."""
        return self.nome

    class Meta:
        managed = False
        db_table = 'setor'


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    fk_id_setor = models.ForeignKey(
        Setor,
        models.DO_NOTHING,
        db_column='fk_id_setor',
        blank=True,
        null=True,
    )

    def __str__(self):
        """Retorna nome do cargo para admin e logs."""
        return self.nome

    class Meta:
        managed = False
        db_table = 'cargo'
