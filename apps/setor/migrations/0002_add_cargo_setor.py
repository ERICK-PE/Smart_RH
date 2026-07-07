from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('setor', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE cargo
                    ADD COLUMN IF NOT EXISTS fk_id_setor integer;

                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'cargo_fk_id_setor_fkey'
                        ) THEN
                            ALTER TABLE cargo
                            ADD CONSTRAINT cargo_fk_id_setor_fkey
                            FOREIGN KEY (fk_id_setor)
                            REFERENCES setor(id_setor)
                            ON DELETE NO ACTION;
                        END IF;
                    END $$;

                    CREATE INDEX IF NOT EXISTS cargo_fk_id_setor_idx
                    ON cargo(fk_id_setor);
                    """,
                    reverse_sql="""
                    ALTER TABLE cargo
                    DROP CONSTRAINT IF EXISTS cargo_fk_id_setor_fkey;

                    DROP INDEX IF EXISTS cargo_fk_id_setor_idx;

                    ALTER TABLE cargo
                    DROP COLUMN IF EXISTS fk_id_setor;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='cargo',
                    name='fk_id_setor',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        db_column='fk_id_setor',
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='setor.setor',
                    ),
                ),
            ],
        ),
    ]
