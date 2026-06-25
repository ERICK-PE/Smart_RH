from django.contrib import admin

from .models import Contrato, Funcionario, FuncionarioAgenteDocumento, PlanoCarreira


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("id_funcionario", "user", "nome", "fk_id_setor", "fk_id_cargo", "data_admissao")
    list_filter = ("fk_id_setor", "fk_id_cargo")
    search_fields = ("nome", "user__username")


@admin.register(PlanoCarreira)
class PlanoCarreiraAdmin(admin.ModelAdmin):
    list_display = ("id_plano", "fk_id_cargo")
    list_filter = ("fk_id_cargo",)


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("id_contrato", "fk_id_funcionario", "tipo_contrato", "data_inicio", "data_fim")
    list_filter = ("tipo_contrato", "data_inicio")
    search_fields = ("fk_id_funcionario__nome",)


@admin.register(FuncionarioAgenteDocumento)
class FuncionarioAgenteDocumentoAdmin(admin.ModelAdmin):
    list_display = ("id_documento", "titulo", "ativo", "criado_por", "criado_em")
    list_filter = ("ativo", "criado_em")
    search_fields = ("titulo", "criado_por__username")
    readonly_fields = ("conteudo_extraido", "criado_em", "atualizado_em")
