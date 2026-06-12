from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('funcionario', '0002_add_funcionario_user'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE funcionario
                    ADD COLUMN IF NOT EXISTS status varchar(20) NOT NULL DEFAULT 'ativo';

                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'funcionario_status_check'
                    ) THEN
                        ALTER TABLE funcionario
                            ADD CONSTRAINT funcionario_status_check
                            CHECK (status IN ('ativo', 'inativo'));
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
