from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('candidato_vaga', '0001_alter_candidato_pk_to_cpf'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE candidato
                ADD COLUMN IF NOT EXISTS user_id integer;

            CREATE UNIQUE INDEX IF NOT EXISTS candidato_user_id_key
                ON candidato(user_id)
                WHERE user_id IS NOT NULL;

            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'candidato_user_id_fkey'
                ) THEN
                    ALTER TABLE candidato
                        ADD CONSTRAINT candidato_user_id_fkey
                        FOREIGN KEY (user_id)
                        REFERENCES auth_user(id)
                        DEFERRABLE INITIALLY DEFERRED;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
