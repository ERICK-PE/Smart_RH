from django.db import models


class Candidato(models.Model):
    id_candidato = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    curriculo = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'candidato'


class Vaga(models.Model):
    id_vaga = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=150, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    fk_id_setor = models.ForeignKey('setor.Setor',
                                     models.DO_NOTHING, 
                                     db_column='fk_id_setor', 
                                     blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vaga'


class CandidatoVaga(models.Model):
    pk = models.CompositePrimaryKey('id_candidato', 'id_vaga')
    id_candidato = models.ForeignKey(Candidato, models.DO_NOTHING, db_column='id_candidato')
    id_vaga = models.ForeignKey(Vaga, models.DO_NOTHING, db_column='id_vaga')
    status_processo = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'candidato_vaga'