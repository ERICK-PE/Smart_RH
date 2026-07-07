from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('funcionario', '0005_contrato_arquivo_folha_pagamento'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE plano_carreira
                    ADD COLUMN IF NOT EXISTS fk_id_criador integer NULL;

                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'plano_carreira_fk_id_criador_fk'
                        ) THEN
                            ALTER TABLE plano_carreira
                            ADD CONSTRAINT plano_carreira_fk_id_criador_fk
                            FOREIGN KEY (fk_id_criador)
                            REFERENCES funcionario(id_funcionario)
                            DEFERRABLE INITIALLY DEFERRED;
                        END IF;
                    END $$;
                    """,
                    reverse_sql="""
                    ALTER TABLE plano_carreira
                    DROP CONSTRAINT IF EXISTS plano_carreira_fk_id_criador_fk;

                    ALTER TABLE plano_carreira
                    DROP COLUMN IF EXISTS fk_id_criador;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='planocarreira',
                    name='fk_id_criador',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        db_column='fk_id_criador',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name='planos_criados',
                        to='funcionario.funcionario',
                    ),
                ),
            ],
        ),
    ]
