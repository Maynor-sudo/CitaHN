
from django.shortcuts import render, get_object_or_404

from apps.hospitales.models import Departamento, Hospital
from apps.medicos.models import Medico


def seleccionar_departamento(request):
    departamentos = Departamento.objects.filter(
        activo=True,
        hospitales__activo=True,
    ).distinct().order_by("nombre")

    return render(
        request,
        "hospitales/departamentos.html",
        {"departamentos": departamentos},
    )


def seleccionar_hospital(request, departamento_id):
    departamento = get_object_or_404(
        Departamento,
        id=departamento_id,
        activo=True,
    )

    hospitales = Hospital.objects.filter(
        departamento=departamento,
        activo=True,
    ).order_by("nombre")

    return render(
        request,
        "hospitales/hospitales.html",
        {
            "departamento": departamento,
            "hospitales": hospitales,
        },
    )


def seleccionar_especialidad(request, hospital_id):
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True,
    )

    especialidades = hospital.especialidades.filter(
        activo=True,
    ).order_by("nombre")

    for especialidad in especialidades:
        especialidad.disponible = Medico.objects.filter(
            hospital=hospital,
            especialidad=especialidad,
            activo=True,
            usuario__activo=True,
        ).exists()

    return render(
        request,
        "hospitales/especialidades.html",
        {
            "hospital": hospital,
            "especialidades": especialidades,
        },
    )
