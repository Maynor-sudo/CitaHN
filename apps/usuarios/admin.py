from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario

    list_display = (
        "identidad",
        "nombre",
        "apellido",
        "rol",
        "activo",
        "fecha_registro",
    )

    list_filter = ("rol", "activo")

    ordering = ("identidad",)

    search_fields = (
        "identidad",
        "nombre",
        "apellido",
        "email",
    )