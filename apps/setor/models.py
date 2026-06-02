from django.db import models


class Setor(models.Model):
    id_setor = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        managed = False
        db_table = 'setor'


class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        managed = False
        db_table = 'cargo'
