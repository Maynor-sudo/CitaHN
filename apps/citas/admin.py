from django.contrib import admin
from .models import Cita


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        "paciente",
        "medico",
        "especialidad",
        "hospital",
        "fecha_hora",
        "estado",
    )

    list_filter = (
        "estado",
        "especialidad",
        "hospital",
    )

    search_fields = (
        "paciente__identidad",
        "paciente__nombre",
        "paciente__apellido",
        "medico__usuario__nombre",
        "medico__usuario__apellido",
    )

    ordering = ("-fecha_hora",)