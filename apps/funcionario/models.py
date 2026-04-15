from django.db import models
from django.db import models


class Funcionario(models.Model):
    id_funcionario = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    cpf = models.CharField(unique=True, max_length=14)
    email = models.CharField(unique=True, max_length=150, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_admissao = models.DateField()
    fk_id_setor = models.ForeignKey('setor.Setor', 
                                    models.DO_NOTHING, 
                                    db_column='fk_id_setor')
    fk_id_cargo = models.ForeignKey('setor.Cargo', 
                                    models.DO_NOTHING, 
                                    db_column='fk_id_cargo')

    class Meta:
        managed = False
        db_table = 'funcionario'


class PlanoCarreira(models.Model):
    id_plano = models.AutoField(primary_key=True)
    fk_id_cargo = models.ForeignKey('setor.Cargo', 
                                    models.DO_NOTHING, 
                                    db_column='fk_id_cargo')
    descricao = models.TextField(blank=True, null=True)
    requisitos = models.TextField(blank=True, null=True)

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

    class Meta:
        managed = False
        db_table = 'contrato'
