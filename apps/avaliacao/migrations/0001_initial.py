import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('funcionario', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnaliseComportamental',
            fields=[
                ('id_analise', models.AutoField(primary_key=True, serialize=False)),
                ('resultado', models.TextField(blank=True, null=True)),
                ('data_analise', models.DateField(blank=True, null=True)),
                ('fk_id_funcionario', models.ForeignKey(db_column='fk_id_funcionario', on_delete=django.db.models.deletion.DO_NOTHING, to='funcionario.funcionario')),
            ],
            options={
                'db_table': 'analise_comportamental',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AvaliacaoDesempenho',
            fields=[
                ('id_avaliacao', models.AutoField(primary_key=True, serialize=False)),
                ('categoria', models.CharField(blank=True, max_length=100, null=True)),
                ('nota', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('data_avaliacao', models.DateField()),
                ('fk_id_funcionario', models.ForeignKey(db_column='fk_id_funcionario', on_delete=django.db.models.deletion.DO_NOTHING, to='funcionario.funcionario')),
                ('fk_id_avaliador', models.ForeignKey(db_column='fk_id_avaliador', on_delete=django.db.models.deletion.DO_NOTHING, related_name='avaliacaodesempenho_fk_id_avaliador_set', to='funcionario.funcionario')),
            ],
            options={
                'db_table': 'avaliacao_desempenho',
                'managed': False,
            },
        ),
    ]
