from django.shortcuts import render
from django.db.models import Q

from apps.medicos.models import Medico
from apps.hospitales.models import Especialidad, Hospital

from django.shortcuts import render


def buscar_especialistas(request):
    tipo = request.GET.get("tipo", "especialidad")
    consulta = request.GET.get("q", "").strip()

    especialidades = (
        Especialidad.objects.filter(
            activo=True,
            hospitales__activo=True,
            hospitales__departamento__activo=True,
            medicos__activo=True,
            medicos__usuario__activo=True,
        )
        .distinct()
        .order_by("nombre")
    )

    hospitales = (
        Hospital.objects.filter(
            activo=True,
            departamento__activo=True,
            medicos__activo=True,
            medicos__usuario__activo=True,
            medicos__especialidad__activo=True,
        )
        .distinct()
        .order_by("nombre")
    )

    resultados = Medico.objects.none()

    if consulta and tipo in ("especialidad", "hospital"):
        filtros = {
            "activo": True,
            "usuario__activo": True,
            "hospital__activo": True,
            "hospital__departamento__activo": True,
            "especialidad__activo": True,
        }

        resultados = Medico.objects.filter(**filtros)

        if tipo == "especialidad":
            resultados = resultados.filter(especialidad__nombre__icontains=consulta)
        else:
            resultados = resultados.filter(hospital__nombre__icontains=consulta)

        resultados = resultados.select_related(
            "usuario",
            "hospital",
            "hospital__departamento",
            "especialidad",
        ).order_by(
            "especialidad__nombre",
            "hospital__nombre",
        )

    return render(
        request,
        "medicos/buscar_especialistas.html",
        {
            "tipo": tipo,
            "consulta": consulta,
            "especialidades": especialidades,
            "hospitales": hospitales,
            "resultados": resultados,
            "busqueda_realizada": bool(consulta),
        },
    )
