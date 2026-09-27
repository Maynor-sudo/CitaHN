from django.shortcuts import render, get_object_or_404
from .models import Departamento, Hospital


def seleccionar_departamento(request):
    departamentos = Departamento.objects.filter(
        activo=True
    ).order_by("nombre")

    return render(
        request,
        "hospitales/departamentos.html",
        {"departamentos": departamentos}
    )


def seleccionar_hospital(request, departamento_id):
    departamento = get_object_or_404(
        Departamento,
        id=departamento_id,
        activo=True
    )

    hospitales = departamento.hospitales.filter(
        activo=True
    ).order_by("nombre")

    return render(
        request,
        "hospitales/hospitales.html",
        {
            "departamento": departamento,
            "hospitales": hospitales,
        }
    )


def seleccionar_especialidad(request, hospital_id):
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True
    )

    especialidades = hospital.especialidades.filter(
        activo=True
    ).order_by("nombre")

    return render(
        request,
        "hospitales/especialidades.html",
        {
            "hospital": hospital,
            "especialidades": especialidades,
        }
    )