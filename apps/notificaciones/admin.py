from django.contrib import admin
from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "tipo",
        "canal",
        "enviada",
        "fecha_creacion",
        "fecha_envio",
    )

    list_filter = (
        "tipo",
        "canal",
        "enviada",
    )

    search_fields = (
        "usuario__identidad",
        "usuario__nombre",
        "usuario__apellido",
        "mensaje",
    )

    ordering = ("-fecha_creacion",)