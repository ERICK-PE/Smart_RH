import apps.funcionario.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funcionario', '0004_funcionarioagentedocumento'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE contrato
                            ADD COLUMN IF NOT EXISTS arquivo varchar(255);

                        CREATE TABLE IF NOT EXISTS folha_pagamento (
                            id_folha serial PRIMARY KEY,
                            fk_id_funcionario integer NOT NULL
                                REFERENCES funcionario(id_funcionario)
                                DEFERRABLE INITIALLY DEFERRED,
                            competencia varchar(20),
                            arquivo varchar(255) NOT NULL,
                            criado_em timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
                        );
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='contrato',
                    name='arquivo',
                    field=models.FileField(
                        blank=True,
                        max_length=255,
                        null=True,
                        upload_to=apps.funcionario.models.contrato_upload_path,
                    ),
                ),
                migrations.CreateModel(
                    name='FolhaPagamento',
                    fields=[
                        ('id_folha', models.AutoField(primary_key=True, serialize=False)),
                        ('competencia', models.CharField(blank=True, max_length=20, null=True)),
                        (
                            'arquivo',
                            models.FileField(
                                max_length=255,
                                upload_to=apps.funcionario.models.folha_pagamento_upload_path,
                            ),
                        ),
                        ('criado_em', models.DateTimeField(auto_now_add=True)),
                        (
                            'fk_id_funcionario',
                            models.ForeignKey(
                                db_column='fk_id_funcionario',
                                on_delete=django.db.models.deletion.DO_NOTHING,
                                to='funcionario.funcionario',
                            ),
                        ),
                    ],
                    options={
                        'db_table': 'folha_pagamento',
                    },
                ),
            ],
        ),
    ]
