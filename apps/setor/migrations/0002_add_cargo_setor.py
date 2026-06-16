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
                    sql='ALTER TABLE cargo ADD COLUMN fk_id_setor integer NULL REFERENCES setor(id_setor);',
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='cargo',
                    name='fk_id_setor',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='fk_id_setor',
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='setor.setor',
                    ),
                ),
            ],
        ),
    ]
