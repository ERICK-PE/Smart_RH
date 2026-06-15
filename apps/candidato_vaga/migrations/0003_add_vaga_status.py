from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidato_vaga', '0002_add_candidato_user'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE vaga ADD COLUMN IF NOT EXISTS status varchar(20);
                    UPDATE vaga
                       SET status = 'aberta'
                     WHERE status IS NULL
                        OR status NOT IN ('aberta', 'andamento', 'fechada', 'cancelada');
                    ALTER TABLE vaga ALTER COLUMN status SET DEFAULT 'aberta';
                    ALTER TABLE vaga ALTER COLUMN status SET NOT NULL;
                    ALTER TABLE vaga DROP CONSTRAINT IF EXISTS vaga_status_check;
                    ALTER TABLE vaga
                        ADD CONSTRAINT vaga_status_check
                        CHECK (status IN ('aberta', 'andamento', 'fechada', 'cancelada'));

                    DROP VIEW IF EXISTS listar_todos_os_candidatos_vaga;
                    CREATE VIEW listar_todos_os_candidatos_vaga AS
                        SELECT
                            c.nome AS candidato,
                            v.titulo AS vaga,
                            v.status AS status_vaga,
                            cv.status_processo
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
                    name='status',
                    field=models.CharField(
                        choices=[
                            ('aberta', 'Aberta'),
                            ('andamento', 'Andamento'),
                            ('fechada', 'Fechada'),
                            ('cancelada', 'Cancelada'),
                        ],
                        default='aberta',
                        max_length=20,
                    ),
                ),
            ],
        ),
    ]
