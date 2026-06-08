import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    DECLARE
                        constraint_name text;
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'candidato'
                              AND column_name = 'id_candidato'
                        ) AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'candidato'
                              AND column_name = 'cpf_candidato'
                        ) THEN
                            ALTER TABLE candidato RENAME COLUMN id_candidato TO cpf_candidato;
                        END IF;

                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'candidato_vaga'
                              AND column_name = 'id_candidato'
                        ) AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'candidato_vaga'
                              AND column_name = 'cpf_candidato'
                        ) THEN
                            ALTER TABLE candidato_vaga RENAME COLUMN id_candidato TO cpf_candidato;
                        END IF;

                        FOR constraint_name IN
                            SELECT con.conname
                            FROM pg_constraint con
                            WHERE con.conrelid = 'candidato_vaga'::regclass
                              AND con.contype = 'f'
                              AND con.confrelid = 'candidato'::regclass
                        LOOP
                            EXECUTE format(
                                'ALTER TABLE candidato_vaga DROP CONSTRAINT %I',
                                constraint_name
                            );
                        END LOOP;

                        SELECT con.conname
                        INTO constraint_name
                        FROM pg_constraint con
                        WHERE con.conrelid = 'candidato_vaga'::regclass
                          AND con.contype = 'p';

                        IF constraint_name IS NOT NULL THEN
                            EXECUTE format(
                                'ALTER TABLE candidato_vaga DROP CONSTRAINT %I',
                                constraint_name
                            );
                        END IF;

                        SELECT con.conname
                        INTO constraint_name
                        FROM pg_constraint con
                        WHERE con.conrelid = 'candidato'::regclass
                          AND con.contype = 'p';

                        IF constraint_name IS NOT NULL THEN
                            EXECUTE format(
                                'ALTER TABLE candidato DROP CONSTRAINT %I',
                                constraint_name
                            );
                        END IF;
                    END $$;

                    DROP VIEW IF EXISTS listar_todos_os_candidatos_vaga;
                    DROP VIEW IF EXISTS listar_todos_os_candidato;

                    ALTER TABLE candidato
                        ALTER COLUMN cpf_candidato TYPE varchar(15)
                        USING cpf_candidato::varchar(15),
                        ALTER COLUMN cpf_candidato SET NOT NULL;

                    ALTER TABLE candidato_vaga
                        ALTER COLUMN cpf_candidato TYPE varchar(15)
                        USING cpf_candidato::varchar(15),
                        ALTER COLUMN cpf_candidato SET NOT NULL;

                    ALTER TABLE candidato
                        ADD CONSTRAINT candidato_pkey PRIMARY KEY (cpf_candidato);

                    ALTER TABLE candidato_vaga
                        ADD CONSTRAINT candidato_vaga_pkey PRIMARY KEY (cpf_candidato, id_vaga);

                    ALTER TABLE candidato_vaga
                        ADD CONSTRAINT candidato_vaga_cpf_candidato_fkey
                        FOREIGN KEY (cpf_candidato)
                        REFERENCES candidato(cpf_candidato);

                    CREATE VIEW listar_todos_os_candidato AS
                        SELECT
                            cpf_candidato,
                            nome,
                            email,
                            telefone,
                            curriculo
                        FROM candidato;

                    CREATE VIEW listar_todos_os_candidatos_vaga AS
                        SELECT
                            c.nome AS candidato,
                            v.titulo AS vaga,
                            cv.status_processo
                        FROM candidato_vaga cv
                        JOIN candidato c ON c.cpf_candidato = cv.cpf_candidato
                        JOIN vaga v ON v.id_vaga = cv.id_vaga;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='Candidato',
                    fields=[
                        ('cpf_candidato', models.CharField(max_length=15, primary_key=True, serialize=False)),
                        ('nome', models.CharField(blank=True, max_length=150, null=True)),
                        ('email', models.CharField(blank=True, max_length=150, null=True)),
                        ('telefone', models.CharField(blank=True, max_length=20, null=True)),
                        ('curriculo', models.TextField(blank=True, null=True)),
                    ],
                    options={
                        'db_table': 'candidato',
                        'managed': False,
                    },
                ),
                migrations.CreateModel(
                    name='Vaga',
                    fields=[
                        ('id_vaga', models.AutoField(primary_key=True, serialize=False)),
                        ('titulo', models.CharField(blank=True, max_length=150, null=True)),
                        ('descricao', models.TextField(blank=True, null=True)),
                        ('data_publicacao', models.DateField(blank=True, null=True)),
                        ('fk_id_setor', models.ForeignKey(blank=True, db_column='fk_id_setor', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='setor.setor')),
                    ],
                    options={
                        'db_table': 'vaga',
                        'managed': False,
                    },
                ),
                migrations.CreateModel(
                    name='CandidatoVaga',
                    fields=[
                        ('pk', models.CompositePrimaryKey('cpf_candidato', 'id_vaga', blank=True, editable=False, primary_key=True, serialize=False)),
                        ('status_processo', models.CharField(blank=True, max_length=50, null=True)),
                        ('cpf_candidato', models.ForeignKey(db_column='cpf_candidato', on_delete=django.db.models.deletion.DO_NOTHING, to='candidato_vaga.candidato')),
                        ('id_vaga', models.ForeignKey(db_column='id_vaga', on_delete=django.db.models.deletion.DO_NOTHING, to='candidato_vaga.vaga')),
                    ],
                    options={
                        'db_table': 'candidato_vaga',
                        'managed': False,
                    },
                ),
            ],
        ),
    ]
