from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('avaliacao', '0001_initial'),
        ('funcionario', '0001_initial'),
        ('setor', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS analise_comportamental_envio (
                        id_envio SERIAL PRIMARY KEY,
                        fk_id_funcionario INTEGER NULL REFERENCES funcionario(id_funcionario),
                        fk_id_setor INTEGER NULL REFERENCES setor(id_setor),
                        titulo VARCHAR(150) NOT NULL DEFAULT 'Analise comportamental',
                        perguntas JSONB NOT NULL,
                        criado_por_id INTEGER NULL REFERENCES auth_user(id) ON DELETE SET NULL,
                        criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS analise_comportamental_resposta (
                        id_resposta SERIAL PRIMARY KEY,
                        fk_id_envio INTEGER NOT NULL REFERENCES analise_comportamental_envio(id_envio) ON DELETE CASCADE,
                        fk_id_funcionario INTEGER NOT NULL REFERENCES funcionario(id_funcionario),
                        respostas JSONB NOT NULL DEFAULT '{}'::jsonb,
                        status VARCHAR(20) NOT NULL DEFAULT 'pendente',
                        respondido_em TIMESTAMP WITH TIME ZONE NULL,
                        CONSTRAINT analise_comportamental_resposta_envio_funcionario_uniq
                            UNIQUE (fk_id_envio, fk_id_funcionario),
                        CONSTRAINT analise_comportamental_resposta_status_check
                            CHECK (status IN ('pendente', 'respondido'))
                    );

                    CREATE INDEX IF NOT EXISTS analise_comportamental_envio_funcionario_idx
                        ON analise_comportamental_envio(fk_id_funcionario);
                    CREATE INDEX IF NOT EXISTS analise_comportamental_envio_setor_idx
                        ON analise_comportamental_envio(fk_id_setor);
                    CREATE INDEX IF NOT EXISTS analise_comportamental_resposta_funcionario_idx
                        ON analise_comportamental_resposta(fk_id_funcionario);
                    CREATE INDEX IF NOT EXISTS analise_comportamental_resposta_status_idx
                        ON analise_comportamental_resposta(status);
                    """,
                    reverse_sql="""
                    DROP TABLE IF EXISTS analise_comportamental_resposta;
                    DROP TABLE IF EXISTS analise_comportamental_envio;
                    """,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='AnaliseComportamentalEnvio',
                    fields=[
                        ('id_envio', models.AutoField(primary_key=True, serialize=False)),
                        ('titulo', models.CharField(default='Analise comportamental', max_length=150)),
                        ('perguntas', models.JSONField()),
                        ('criado_em', models.DateTimeField(auto_now_add=True)),
                        ('criado_por', models.ForeignKey(blank=True, db_column='criado_por_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                        ('fk_id_funcionario', models.ForeignKey(blank=True, db_column='fk_id_funcionario', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='funcionario.funcionario')),
                        ('fk_id_setor', models.ForeignKey(blank=True, db_column='fk_id_setor', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='setor.setor')),
                    ],
                    options={
                        'db_table': 'analise_comportamental_envio',
                        'managed': False,
                    },
                ),
                migrations.CreateModel(
                    name='AnaliseComportamentalResposta',
                    fields=[
                        ('id_resposta', models.AutoField(primary_key=True, serialize=False)),
                        ('respostas', models.JSONField(default=dict)),
                        ('status', models.CharField(choices=[('pendente', 'Pendente'), ('respondido', 'Respondido')], default='pendente', max_length=20)),
                        ('respondido_em', models.DateTimeField(blank=True, null=True)),
                        ('fk_id_envio', models.ForeignKey(db_column='fk_id_envio', on_delete=django.db.models.deletion.DO_NOTHING, related_name='respostas', to='avaliacao.analisecomportamentalenvio')),
                        ('fk_id_funcionario', models.ForeignKey(db_column='fk_id_funcionario', on_delete=django.db.models.deletion.DO_NOTHING, to='funcionario.funcionario')),
                    ],
                    options={
                        'db_table': 'analise_comportamental_resposta',
                        'managed': False,
                        'constraints': [models.UniqueConstraint(fields=('fk_id_envio', 'fk_id_funcionario'), name='analise_comportamental_resposta_envio_funcionario_uniq')],
                    },
                ),
            ],
        ),
    ]
