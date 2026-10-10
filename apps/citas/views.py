from functools import wraps
from io import BytesIO

from django.http import HttpResponse
from django.utils.dateparse import parse_date
from apps.notificaciones.models import Notificacion
from apps.citas.models import OfertaCita
from apps.citas.services import aceptar_oferta, rechazar_oferta

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

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
            date.fromisoformat(fecha) if fecha else timezone.localdate()
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
    citas = (
        Cita.objects.filter(
            paciente=request.user,
        )
        .select_related(
            "hospital",
            "especialidad",
            "medico",
            "medico__usuario",
        )
        .order_by("-fecha_hora")
    )

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
            "No puedes cancelar una cita con menos de " "12 horas de anticipación.",
        )
        return redirect("mis_citas")

    messages.success(request, "La cita fue cancelada correctamente.")
    return redirect("mis_citas")


def medico_requerido(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.rol != "MEDICO":
            messages.error(
                request,
                "No tienes permiso para acceder al panel médico.",
            )
            return redirect("inicio")

        try:
            medico = request.user.perfil_medico
        except Medico.DoesNotExist:
            messages.error(
                request,
                "Tu usuario no tiene un perfil médico registrado.",
            )
            return redirect("inicio")

        if not medico.activo or not request.user.activo:
            messages.error(
                request,
                "Tu cuenta médica está inactiva.",
            )
            return redirect("inicio")

        request.medico = medico
        return view_func(request, *args, **kwargs)

    return wrapper


def fechas_agenda(request):
    desde_texto = request.GET.get("desde", "")
    hasta_texto = request.GET.get("hasta", "")

    hoy = timezone.localdate()

    desde = parse_date(desde_texto) if desde_texto else hoy
    hasta = parse_date(hasta_texto) if hasta_texto else hoy

    if desde is None or hasta is None or desde > hasta:
        return None, None

    return desde, hasta


@medico_requerido
def agenda_medico(request):
    desde, hasta = fechas_agenda(request)

    if desde is None:
        messages.error(
            request,
            "El rango de fechas no es válido.",
        )
        return redirect("agenda_medico")

    citas = (
        Cita.objects.filter(
            medico=request.medico,
            fecha_hora__date__gte=desde,
            fecha_hora__date__lte=hasta,
        )
        .select_related(
            "paciente",
            "hospital",
            "especialidad",
        )
        .order_by("fecha_hora")
    )

    return render(
        request,
        "medicos/agenda.html",
        {
            "medico": request.medico,
            "citas": citas,
            "desde": desde,
            "hasta": hasta,
            "hoy": timezone.localdate(),
        },
    )


@medico_requerido
def actualizar_estado_cita(request, cita_id):
    if request.method != "POST":
        return redirect("agenda_medico")

    cita = get_object_or_404(
        Cita,
        id=cita_id,
        medico=request.medico,
    )

    estado_nuevo = request.POST.get("estado")
    hoy = timezone.localdate()

    if estado_nuevo not in [
        Cita.Estado.ATENDIDA,
        Cita.Estado.NO_ASISTIO,
    ]:
        messages.error(request, "El estado solicitado no es válido.")
        return redirect("agenda_medico")

    if cita.fecha_hora.date() > hoy:
        messages.error(
            request,
            "No puedes registrar asistencia para una cita futura.",
        )
        return redirect("agenda_medico")

    if cita.estado not in [
        Cita.Estado.PENDIENTE,
        Cita.Estado.CONFIRMADA,
    ]:
        messages.error(
            request,
            "Esta cita ya fue procesada o está cancelada.",
        )
        return redirect("agenda_medico")

    cita.estado = estado_nuevo
    cita.save(update_fields=["estado", "fecha_actualizacion"])

    messages.success(
        request,
        f"Estado actualizado: {cita.get_estado_display()}.",
    )

    return redirect("agenda_medico")


@medico_requerido
def reporte_pdf_medico(request):
    desde, hasta = fechas_agenda(request)

    if desde is None:
        messages.error(
            request,
            "Selecciona un rango de fechas válido.",
        )
        return redirect("agenda_medico")

    citas = (
        Cita.objects.filter(
            medico=request.medico,
            fecha_hora__date__gte=desde,
            fecha_hora__date__lte=hasta,
        )
        .select_related(
            "paciente",
            "hospital",
            "especialidad",
        )
        .order_by("fecha_hora")
    )

    respuesta = HttpResponse(content_type="application/pdf")
    respuesta["Content-Disposition"] = (
        f'attachment; filename="agenda_medica_{desde}_{hasta}.pdf"'
    )

    documento = SimpleDocTemplate(
        respuesta,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    estilos = getSampleStyleSheet()
    elementos = []

    titulo = ParagraphStyle(
        "TituloAgenda",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#12345A"),
    )

    elementos.append(Paragraph("CitaHN - Agenda médica", titulo))
    elementos.append(Spacer(1, 8))

    nombre_medico = (
        f"{request.medico.usuario.nombre} " f"{request.medico.usuario.apellido}"
    )

    elementos.append(
        Paragraph(
            f"<b>Médico:</b> {nombre_medico}",
            estilos["Normal"],
        )
    )
    elementos.append(
        Paragraph(
            f"<b>Hospital:</b> {request.medico.hospital.nombre}",
            estilos["Normal"],
        )
    )
    elementos.append(
        Paragraph(
            f"<b>Especialidad:</b> {request.medico.especialidad.nombre}",
            estilos["Normal"],
        )
    )
    elementos.append(
        Paragraph(
            f"<b>Período:</b> {desde.strftime('%d/%m/%Y')} al "
            f"{hasta.strftime('%d/%m/%Y')}",
            estilos["Normal"],
        )
    )
    elementos.append(Spacer(1, 12))

    datos = [
        [
            "Fecha y hora",
            "Paciente",
            "Identidad",
            "Motivo",
            "Estado",
        ]
    ]

    for cita in citas:
        paciente = f"{cita.paciente.nombre} " f"{cita.paciente.apellido}"

        datos.append(
            [
                cita.fecha_hora.strftime("%d/%m/%Y %H:%M"),
                paciente,
                cita.paciente.identidad,
                cita.motivo,
                cita.get_estado_display(),
            ]
        )

    if not citas:
        elementos.append(
            Paragraph(
                "No hay citas registradas en este período.",
                estilos["Normal"],
            )
        )
    else:
        tabla = Table(
            datos,
            repeatRows=1,
            colWidths=[3.2 * cm, 4.5 * cm, 3.0 * cm, 7.0 * cm, 3.0 * cm],
        )

        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12345A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor("#F0F4F8"),
                        ],
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        elementos.append(tabla)

    documento.build(elementos)
    return respuesta



@login_required
def mis_notificaciones(request):
    Notificacion.objects.filter(
        usuario=request.user,
        leida=False,
    ).update(leida=True)

    notificaciones = (
        Notificacion.objects.filter(
            usuario=request.user,
        )
        .select_related("oferta_cita")
        .order_by("-fecha_creacion")
    )

    return render(
        request,
        "notificaciones/mis_notificaciones.html",
        {"notificaciones": notificaciones},
    )



@login_required
def aceptar_oferta_view(request, oferta_id):
    if request.method != "POST":
        return redirect("mis_notificaciones")

    oferta = get_object_or_404(
        OfertaCita,
        id=oferta_id,
        paciente=request.user,
    )

    if aceptar_oferta(oferta):
        messages.success(
            request,
            "La oferta fue aceptada y tu cita se actualizó.",
        )
    else:
        messages.error(
            request,
            "No se pudo aceptar la oferta. Puede que ya no esté disponible.",
        )

    return redirect("mis_notificaciones")


@login_required
def rechazar_oferta_view(request, oferta_id):
    if request.method != "POST":
        return redirect("mis_notificaciones")

    oferta = get_object_or_404(
        OfertaCita,
        id=oferta_id,
        paciente=request.user,
    )

    if rechazar_oferta(oferta):
        messages.success(request, "Has rechazado la oferta.")
    else:
        messages.error(
            request,
            "Esta oferta ya fue procesada.",
        )

    return redirect("mis_notificaciones")
