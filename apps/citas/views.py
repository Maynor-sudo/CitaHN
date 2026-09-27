from datetime import date, datetime
from apps.hospitales.models import Hospital, Especialidad
from apps.citas.services import buscar_siguiente_slot
from django.shortcuts import render, get_object_or_404, redirect
from apps.citas.services import obtener_horarios_disponibles
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from apps.citas.services import crear_cita
from django.utils import timezone
from apps.citas.models import Cita

@login_required
def confirmar_cita(request, hospital_id, especialidad_id):
    print("ENTRÓ A CONFIRMAR CITA")
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True
    )

    especialidad = get_object_or_404(
        Especialidad,
        id=especialidad_id,
        activo=True
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
        }
    )

@login_required
def crear_cita_view(request, hospital_id, especialidad_id):
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True
    )

    especialidad = get_object_or_404(
        Especialidad,
        id=especialidad_id,
        activo=True
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
        messages.error(
            request,
            "Todos los campos son obligatorios."
        )
        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    try:
        fecha_hora = datetime.strptime(
            f"{fecha} {hora}",
            "%Y-%m-%d %H:%M"
        )

        fecha_hora = timezone.make_aware(fecha_hora)

    except ValueError:
        messages.error(
            request,
            "La fecha u hora seleccionada no es válida."
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
            "El horario seleccionado ya no está disponible."
        )

        return redirect(
            "seleccionar_horario",
            hospital_id=hospital.id,
            especialidad_id=especialidad.id,
        )

    return render(
        request,
        "citas/cita_creada.html",
        {"cita": cita}
    )


def seleccionar_horario(request, hospital_id, especialidad_id):
    hospital = get_object_or_404(
        Hospital,
        id=hospital_id,
        activo=True
    )

    especialidad = get_object_or_404(
        Especialidad,
        id=especialidad_id,
        activo=True
    )

    fecha = request.GET.get("fecha")

    if fecha:
        try:
            fecha_seleccionada = date.fromisoformat(fecha)
        except ValueError:
            fecha_seleccionada = date.today()
    else:
        fecha_seleccionada = date.today()

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
        }
    )

@login_required
def mis_citas(request):
    citas = Cita.objects.filter(
        paciente=request.user
    ).select_related(
        "hospital",
        "especialidad",
        "medico",
        "medico__usuario",
    ).order_by("-fecha_hora")

    return render(
        request,
        "citas/mis_citas.html",
        {
            "citas": citas,
        }
    )
    
@login_required
def cancelar_cita_view(request, cita_id):
    cita = get_object_or_404(
        Cita,
        id=cita_id,
        paciente=request.user
    )

    if request.method != "POST":
        return redirect("mis_citas")

    if cita.estado not in [
        Cita.Estado.PENDIENTE,
        Cita.Estado.CONFIRMADA,
    ]:
        messages.error(
            request,
            "Esta cita no se puede cancelar."
        )
        return redirect("mis_citas")

    ahora = timezone.now()
    limite = cita.fecha_hora - timezone.timedelta(hours=12)

    if ahora > limite:
        messages.error(
            request,
            "No puedes cancelar una cita con menos de 12 horas de anticipación."
        )
        return redirect("mis_citas")

    cita.estado = Cita.Estado.CANCELADA
    cita.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )

    messages.success(
        request,
        "La cita fue cancelada correctamente."
    )

    return redirect("mis_citas")