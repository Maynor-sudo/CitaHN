from django.contrib import admin
from .models import Departamento, Hospital, Especialidad


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "departamento", "telefono", "activo")
    list_filter = ("departamento", "activo")
    search_fields = ("nombre", "direccion")