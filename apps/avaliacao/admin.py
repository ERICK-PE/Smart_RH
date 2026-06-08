from django.contrib import admin

from .models import AnaliseComportamental, AvaliacaoDesempenho


@admin.register(AnaliseComportamental)
class AnaliseComportamentalAdmin(admin.ModelAdmin):
    list_display = ("id_analise", "fk_id_funcionario", "data_analise")
    list_filter = ("data_analise",)
    search_fields = ("fk_id_funcionario__nome",)


@admin.register(AvaliacaoDesempenho)
class AvaliacaoDesempenhoAdmin(admin.ModelAdmin):
    list_display = ("id_avaliacao", "fk_id_funcionario", "fk_id_avaliador", "categoria", "nota", "data_avaliacao")
    list_filter = ("categoria", "data_avaliacao")
    search_fields = ("fk_id_funcionario__nome", "fk_id_avaliador__nome")
