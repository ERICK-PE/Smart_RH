from django.conf import settings
from django.db import models


class AnaliseComportamental(models.Model):
    id_analise = models.AutoField(primary_key=True)
    fk_id_funcionario = models.ForeignKey('funcionario.Funcionario',
                                           models.DO_NOTHING,
                                            db_column='fk_id_funcionario')
    resultado = models.TextField(blank=True, null=True)
    data_analise = models.DateField(blank=True, null=True)

    def __str__(self):
        """Retorna identificador da analise sem expor resultado."""
        return f'Analise comportamental {self.id_analise}'

    class Meta:
        managed = False
        db_table = 'analise_comportamental'


class AnaliseComportamentalEnvio(models.Model):
    id_envio = models.AutoField(primary_key=True)
    fk_id_funcionario = models.ForeignKey(
        'funcionario.Funcionario',
        models.DO_NOTHING,
        db_column='fk_id_funcionario',
        blank=True,
        null=True,
    )
    fk_id_setor = models.ForeignKey(
        'setor.Setor',
        models.DO_NOTHING,
        db_column='fk_id_setor',
        blank=True,
        null=True,
    )
    titulo = models.CharField(max_length=150, default='Analise comportamental')
    perguntas = models.JSONField()
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        db_column='criado_por_id',
        blank=True,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Retorna identificador do envio sem expor respostas."""
        return f'Envio de analise comportamental {self.id_envio}'

    class Meta:
        managed = False
        db_table = 'analise_comportamental_envio'


class AnaliseComportamentalResposta(models.Model):
    STATUS_PENDENTE = 'pendente'
    STATUS_RESPONDIDO = 'respondido'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_RESPONDIDO, 'Respondido'),
    ]

    id_resposta = models.AutoField(primary_key=True)
    fk_id_envio = models.ForeignKey(
        AnaliseComportamentalEnvio,
        models.DO_NOTHING,
        db_column='fk_id_envio',
        related_name='respostas',
    )
    fk_id_funcionario = models.ForeignKey(
        'funcionario.Funcionario',
        models.DO_NOTHING,
        db_column='fk_id_funcionario',
    )
    respostas = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    respondido_em = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        """Retorna identificador da resposta sem expor conteudo."""
        return f'Resposta de analise comportamental {self.id_resposta}'

    class Meta:
        managed = False
        db_table = 'analise_comportamental_resposta'
        constraints = [
            models.UniqueConstraint(
                fields=['fk_id_envio', 'fk_id_funcionario'],
                name='analise_comportamental_resposta_envio_funcionario_uniq',
            ),
        ]


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
        """Retorna id da avaliacao"""
        return f'Avaliacao de desempenho {self.id_avaliacao}'

    class Meta:
        managed = False
        db_table = 'avaliacao_desempenho'
