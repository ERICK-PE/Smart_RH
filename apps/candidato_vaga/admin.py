from django.contrib import admin

from .models import Candidato, Vaga


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ("id_candidato", "nome")
    search_fields = ("nome",)


@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = ("id_vaga", "titulo", "fk_id_setor", "data_publicacao")
    list_filter = ("fk_id_setor", "data_publicacao")
    search_fields = ("titulo",)
