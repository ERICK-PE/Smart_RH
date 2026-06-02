from django.db import models


class AnaliseComportamental(models.Model):
    id_analise = models.AutoField(primary_key=True)
    fk_id_funcionario = models.ForeignKey('funcionario.Funcionario',
                                           models.DO_NOTHING,
                                            db_column='fk_id_funcionario')
    resultado = models.TextField(blank=True, null=True)
    data_analise = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'Analise comportamental {self.id_analise}'

    class Meta:
        managed = False
        db_table = 'analise_comportamental'


class AvaliacaoDesempenho(models.Model):
    id_avaliacao = models.AutoField(primary_key=True)
    fk_id_funcionario = models.ForeignKey('funcionario.Funcionario', 
                                          models.DO_NOTHING, 
                                          db_column='fk_id_funcionario')
    fk_id_avaliador = models.ForeignKey('funcionario.Funcionario', 
                                        models.DO_NOTHING, 
                                        db_column='fk_id_avaliador', 
                                        related_name='avaliacaodesempenho_fk_id_avaliador_set')
    categoria = models.CharField(max_length=100, blank=True, null=True)
    nota = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    comentario = models.TextField(blank=True, null=True)
    data_avaliacao = models.DateField()

    def __str__(self):
        return f'Avaliacao de desempenho {self.id_avaliacao}'

    class Meta:
        managed = False
        db_table = 'avaliacao_desempenho'
