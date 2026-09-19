from django.contrib import admin
from .models import Medico, Disponibilidad, BloqueoHorario


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "especialidad",
        "hospital",
        "numero_colegiacion",
        "activo",
    )
    list_filter = ("especialidad", "hospital", "activo")
    search_fields = (
        "usuario__identidad",
        "usuario__nombre",
        "usuario__apellido",
        "numero_colegiacion",
    )


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = (
        "medico",
        "dia_semana",
        "hora_inicio",
        "hora_fin",
        "activo",
    )
    list_filter = ("dia_semana", "activo")


@admin.register(BloqueoHorario)
class BloqueoHorarioAdmin(admin.ModelAdmin):
    list_display = (
        "medico",
        "inicio",
        "fin",
        "motivo",
    )
    list_filter = ("medico",)
    search_fields = (
        "medico__usuario__nombre",
        "medico__usuario__apellido",
        "motivo",
    )