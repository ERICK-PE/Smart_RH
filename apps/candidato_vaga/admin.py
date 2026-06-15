from django.contrib import admin

from .models import Candidato, Vaga


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ("cpf_candidato", "nome")
    search_fields = ("cpf_candidato", "nome")


@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = ("id_vaga", "titulo", "status", "fk_id_setor", "data_publicacao")
    list_filter = ("status", "fk_id_setor", "data_publicacao")
    search_fields = ("titulo",)
