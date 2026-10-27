
from django.shortcuts import render
from django.db.models import Q

from apps.medicos.models import Medico
from apps.hospitales.models import Especialidad


def buscar_especialistas(request):
    consulta = request.GET.get("q", "").strip()
    especialidades = Especialidad.objects.filter(
        activo=True,
        hospitales__activo=True,
        hospitales__departamento__activo=True,
        medicos__activo=True,
        medicos__usuario__activo=True,
    ).distinct().order_by("nombre")

    resultados = Medico.objects.none()

    if consulta:
        resultados = (
            Medico.objects.filter(
                Q(especialidad__nombre__icontains=consulta)
                | Q(usuario__nombre__icontains=consulta)
                | Q(usuario__apellido__icontains=consulta),
                activo=True,
                usuario__activo=True,
                hospital__activo=True,
                hospital__departamento__activo=True,
                especialidad__activo=True,
            )
            .select_related(
                "usuario",
                "hospital",
                "hospital__departamento",
                "especialidad",
            )
            .order_by(
                "especialidad__nombre",
                "hospital__departamento__nombre",
                "hospital__nombre",
                "usuario__apellido",
            )
        )

    return render(
        request,
        "medicos/buscar_especialistas.html",
        {
            "consulta": consulta,
            "especialidades": especialidades,
            "resultados": resultados,
        },
    )
