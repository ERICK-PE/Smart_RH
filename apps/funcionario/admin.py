from django.contrib import admin

from .models import Contrato, Funcionario, PlanoCarreira


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("id_funcionario", "nome", "fk_id_setor", "fk_id_cargo", "data_admissao")
    list_filter = ("fk_id_setor", "fk_id_cargo")
    search_fields = ("nome",)


@admin.register(PlanoCarreira)
class PlanoCarreiraAdmin(admin.ModelAdmin):
    list_display = ("id_plano", "fk_id_cargo")
    list_filter = ("fk_id_cargo",)


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("id_contrato", "fk_id_funcionario", "tipo_contrato", "data_inicio", "data_fim")
    list_filter = ("tipo_contrato", "data_inicio")
    search_fields = ("fk_id_funcionario__nome",)
