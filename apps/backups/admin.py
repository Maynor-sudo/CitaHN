from django.contrib import admin
from django.urls import path

from .models import Backup
from .views import descargar_backup


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_archivo",
        "fecha_creacion",
        "tamano",
        "creado_por",
    )

    readonly_fields = (
        "nombre_archivo",
        "fecha_creacion",
        "tamano",
        "creado_por",
    )

    change_list_template = "admin/backups/backup/change_list.html"

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "generar/",
                self.admin_site.admin_view(descargar_backup),
                name="backups_backup_generar",
            ),
        ]

        return custom_urls + urls

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False