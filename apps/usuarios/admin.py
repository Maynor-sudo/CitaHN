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

    list_filter = (
        "rol",
        "activo",
    )

    ordering = ("identidad",)

    search_fields = (
        "identidad",
        "nombre",
        "apellido",
        "email",
    )

    fieldsets = (
        ("Información personal", {
            "fields": (
                "identidad",
                "nombre",
                "apellido",
                "email",
                "telefono",
                "fecha_nacimiento",
            )
        }),
        ("Rol y estado", {
            "fields": (
                "rol",
                "activo",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Seguridad", {
            "fields": (
                "password",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "identidad",
                "nombre",
                "apellido",
                "email",
                "telefono",
                "fecha_nacimiento",
                "rol",
                "password1",
                "password2",
                "activo",
            ),
        }),
    )