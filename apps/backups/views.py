
import os
import re

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import FileResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Backup
from .services import generar_backup


@permission_required("backups.add_backup", raise_exception=True)
@require_POST
def descargar_backup(request):
    ruta = None

    try:
        nombre_base = request.POST.get("nombre_backup", "").strip()

        if not nombre_base:
            messages.error(request, "Debes ingresar un nombre para el backup.")
            return redirect(
                reverse("admin:backups_backup_changelist")
            )

        # Evitar caracteres peligrosos en el nombre
        nombre_base = re.sub(r"[^\w-]+", "_", nombre_base)
        nombre_base = nombre_base.strip("_-")[:120]

        if not nombre_base:
            messages.error(request, "El nombre ingresado no es válido.")
            return redirect(
                reverse("admin:backups_backup_changelist")
            )

        # Agregar fecha y hora automáticamente
        fecha = timezone.localtime().strftime("%Y%m%d_%H%M%S")

        nombre = f"{nombre_base}_{fecha}.dump.enc"

        ruta = generar_backup()
        tamano = os.path.getsize(ruta)

        Backup.objects.create(
            nombre_archivo=nombre,
            tamano=tamano,
            creado_por=request.user,
        )

        archivo = open(ruta, "rb")

        respuesta = FileResponse(
            archivo,
            as_attachment=True,
            filename=nombre,
        )

        def limpiar_archivo():
            if os.path.exists(ruta):
                os.remove(ruta)

        respuesta._resource_closers.append(limpiar_archivo)

        return respuesta

    except Exception:
        if ruta and os.path.exists(ruta):
            os.remove(ruta)

        messages.error(
            request,
            "No fue posible generar la copia de seguridad."
        )

        return redirect(
            reverse("admin:backups_backup_changelist")
        )
