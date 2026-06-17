from django.db import migrations, models

import apps.candidato_vaga.models


class Migration(migrations.Migration):

    dependencies = [
        ('candidato_vaga', '0003_add_vaga_status'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='candidato',
                    name='curriculo',
                    field=models.FileField(
                        blank=True,
                        max_length=255,
                        null=True,
                        upload_to=apps.candidato_vaga.models.candidato_curriculo_upload_path,
                    ),
                ),
            ],
        ),
    ]
