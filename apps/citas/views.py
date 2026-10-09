
from datetime import date, datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.hospitales.models import Hospital
from apps.medicos.models import Medico
from apps.citas.models import Cita
from apps.citas.services import (
    obtener_horarios_disponibles,
    crear_cita,
    cancelar_cita,
)


def especialidad_con_medicos(hospital, especialidad):
    return Medico.objects.filter(
        hospital=hospital,
        especialidad=especialidad,
        activo=True,
        usuario__activo=True,
    ).exists()


def obtener_especialidad(hospital, especialidad_id):
    return get_object_or_404(
        hospital.especialidades.filter(activo=True),
        id=especialidad_id,
    )


def seleccionar_horario(request, hospital_id, especialidad_id):
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True,
    )
    especialidad = obtener_especialidad(hospital, especialidad_id)

    if not especialidad_con_medicos(hospital, especialidad):
        messages.warning(
            request,
            "Esta especialidad estará disponible próximamente.",
        )
        return render(
            request,
            "citas/horarios.html",
            {
                "hospital": hospital,
                "especialidad": especialidad,
                "fecha": timezone.localdate(),
                "horarios": [],
                "sin_medicos": True,
            },
        )

    fecha = request.GET.get("fecha")

    try:
        fecha_seleccionada = (
            date.fromisoformat(fecha)
            if fecha
            else timezone.localdate()
        )
    except ValueError:
        fecha_seleccionada = timezone.localdate()

    horarios = obtener_horarios_disponibles(
        especialidad,
        hospital,
        fecha_seleccionada,
    )

    return render(
        request,
        "citas/horarios.html",
        {
            "hospital": hospital,
            "especialidad": especialidad,
            "fecha": fecha_seleccionada,
            "horarios": horarios,
            "sin_medicos": False,
        },
    )


@login_required
def confirmar_cita(request, hospital_id, especialidad_id):
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True,
    )
    especialidad = obtener_especialidad(hospital, especialidad_id)

    if not especialidad_con_medicos(hospital, especialidad):
        messages.warning(
            request,
            "Esta especialidad estará disponible próximamente.",
        )
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    fecha = request.GET.get("fecha")
    hora = request.GET.get("hora")

    if not fecha or not hora:
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    try:
        fecha_seleccionada = date.fromisoformat(fecha)
    except ValueError:
        messages.error(request, "La fecha seleccionada no es válida.")
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    return render(
        request,
        "citas/confirmar.html",
        {
            "hospital": hospital,
            "especialidad": especialidad,
            "fecha": fecha_seleccionada,
            "hora": hora,
        },
    )


@login_required
def crear_cita_view(request, hospital_id, especialidad_id):
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True,
    )
    especialidad = obtener_especialidad(hospital, especialidad_id)

    if not especialidad_con_medicos(hospital, especialidad):
        messages.warning(
            request,
            "Esta especialidad estará disponible próximamente.",
        )
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    if request.method != "POST":
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    fecha = request.POST.get("fecha")
    hora = request.POST.get("hora")
    motivo = request.POST.get("motivo", "").strip()

    if not fecha or not hora or not motivo:
        messages.error(request, "Todos los campos son obligatorios.")
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    try:
        fecha_hora = datetime.strptime(
            f"{fecha} {hora}",
            "%Y-%m-%d %H:%M",
        )
        fecha_hora = timezone.make_aware(fecha_hora)
    except ValueError:
        messages.error(
            request,
            "La fecha u hora seleccionada no es válida.",
        )
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    cita = crear_cita(
        paciente=request.user,
        especialidad=especialidad,
        hospital=hospital,
        fecha_hora=fecha_hora,
        motivo=motivo,
    )

    if cita is None:
        messages.error(
            request,
            "El horario seleccionado ya no está disponible.",
        )
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    return render(
        request,
        "citas/cita_creada.html",
        {"cita": cita},
    )


@login_required
def mis_citas(request):
    citas = Cita.objects.filter(
        paciente=request.user,
    ).select_related(
        "hospital",
        "especialidad",
        "medico",
        "medico__usuario",
    ).order_by("-fecha_hora")

    return render(
        request,
        "citas/mis_citas.html",
        {"citas": citas},
    )


@login_required
def cancelar_cita_view(request, cita_id):
    cita = get_object_or_404(
        Cita,
        id=cita_id,
        paciente=request.user,
    )

    if request.method != "POST":
        return redirect("mis_citas")

    if cita.estado not in [
        Cita.Estado.PENDIENTE,
        Cita.Estado.CONFIRMADA,
    ]:
        messages.error(request, "Esta cita no se puede cancelar.")
        return redirect("mis_citas")

    cancelada = cancelar_cita(cita)

    if not cancelada:
        messages.error(
            request,
            "No puedes cancelar una cita con menos de "
            "12 horas de anticipación.",
        )
        return redirect("mis_citas")

    messages.success(request, "La cita fue cancelada correctamente.")
    return redirect("mis_citas")
