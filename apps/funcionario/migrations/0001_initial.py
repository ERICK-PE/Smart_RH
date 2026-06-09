import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('setor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Funcionario',
            fields=[
                ('id_funcionario', models.AutoField(primary_key=True, serialize=False)),
                ('user', models.OneToOneField(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='funcionario', to=settings.AUTH_USER_MODEL)),
                ('nome', models.CharField(max_length=150)),
                ('cpf', models.CharField(max_length=14, unique=True)),
                ('email', models.CharField(blank=True, max_length=150, null=True, unique=True)),
                ('telefone', models.CharField(blank=True, max_length=20, null=True)),
                ('data_admissao', models.DateField()),
                ('fk_id_setor', models.ForeignKey(db_column='fk_id_setor', on_delete=django.db.models.deletion.DO_NOTHING, to='setor.setor')),
                ('fk_id_cargo', models.ForeignKey(db_column='fk_id_cargo', on_delete=django.db.models.deletion.DO_NOTHING, to='setor.cargo')),
            ],
            options={
                'db_table': 'funcionario',
                'permissions': [
                    ('view_lideranca', 'Pode acessar recursos de leitura da lideranca'),
                    ('manage_lideranca', 'Pode gerenciar recursos da lideranca'),
                    ('view_rh_panel', 'Pode acessar paineis de RH'),
                    ('manage_rh', 'Pode gerenciar recursos de RH'),
                ],
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanoCarreira',
            fields=[
                ('id_plano', models.AutoField(primary_key=True, serialize=False)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('requisitos', models.TextField(blank=True, null=True)),
                ('fk_id_cargo', models.ForeignKey(db_column='fk_id_cargo', on_delete=django.db.models.deletion.DO_NOTHING, to='setor.cargo')),
            ],
            options={
                'db_table': 'plano_carreira',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Contrato',
            fields=[
                ('id_contrato', models.AutoField(primary_key=True, serialize=False)),
                ('tipo_contrato', models.CharField(blank=True, max_length=50, null=True)),
                ('salario', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('data_inicio', models.DateField()),
                ('data_fim', models.DateField(blank=True, null=True)),
                ('fk_id_funcionario', models.ForeignKey(db_column='fk_id_funcionario', on_delete=django.db.models.deletion.DO_NOTHING, to='funcionario.funcionario')),
            ],
            options={
                'db_table': 'contrato',
                'managed': False,
            },
        ),
    ]
