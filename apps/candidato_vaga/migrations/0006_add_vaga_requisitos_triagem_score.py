from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidato_vaga', '0005_add_candidatura_triagem'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE vaga
                        ADD COLUMN IF NOT EXISTS requisitos text;
                    ALTER TABLE candidato_vaga
                        ADD COLUMN IF NOT EXISTS triagem_automatica_pontuacao smallint;
                    ALTER TABLE candidato_vaga
                        ADD COLUMN IF NOT EXISTS triagem_automatica_classificacao varchar(40);

                    DROP VIEW IF EXISTS listar_todos_os_candidatos_vaga;
                    CREATE VIEW listar_todos_os_candidatos_vaga AS
                        SELECT
                            c.nome AS candidato,
                            v.titulo AS vaga,
                            v.status AS status_vaga,
                            v.requisitos AS requisitos_vaga,
                            cv.status_processo,
                            cv.triagem_automatica_aprovada,
                            cv.triagem_automatica_motivo,
                            cv.triagem_automatica_palavras_chave,
                            cv.triagem_automatica_pontuacao,
                            cv.triagem_automatica_classificacao
                        FROM candidato_vaga cv
                        JOIN candidato c ON cv.cpf_candidato = c.cpf_candidato
                        JOIN vaga v ON cv.id_vaga = v.id_vaga;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='vaga',
                    name='requisitos',
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='candidatovaga',
                    name='triagem_automatica_pontuacao',
                    field=models.PositiveSmallIntegerField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='candidatovaga',
                    name='triagem_automatica_classificacao',
                    field=models.CharField(blank=True, max_length=40, null=True),
                ),
            ],
        ),
    ]
