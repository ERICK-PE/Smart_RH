from django.contrib import admin

from .models import Cargo, Setor


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ("id_setor", "nome")
    search_fields = ("nome",)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("id_cargo", "nome")
    search_fields = ("nome",)
