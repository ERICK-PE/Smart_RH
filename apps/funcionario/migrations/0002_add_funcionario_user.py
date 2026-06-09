from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('funcionario', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE funcionario
                ADD COLUMN IF NOT EXISTS user_id integer;

            CREATE UNIQUE INDEX IF NOT EXISTS funcionario_user_id_key
                ON funcionario(user_id)
                WHERE user_id IS NOT NULL;

            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'funcionario_user_id_fkey'
                ) THEN
                    ALTER TABLE funcionario
                        ADD CONSTRAINT funcionario_user_id_fkey
                        FOREIGN KEY (user_id)
                        REFERENCES auth_user(id)
                        DEFERRABLE INITIALLY DEFERRED;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
