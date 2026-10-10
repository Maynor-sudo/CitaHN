
from django.utils import timezone

from apps.notificaciones.models import Notificacion
from apps.citas.models import Cita


def crear_notificacion(usuario, tipo, mensaje):
    return Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        canal=Notificacion.Canal.EMAIL,
        mensaje=mensaje,
        enviada=False,
    )


def notificar_oferta_cita(oferta):
    horario = oferta.horario_liberado
    fecha_nueva = timezone.localtime(horario.fecha_hora)

    cita_actual = Cita.objects.filter(
        paciente=oferta.paciente,
        hospital=horario.hospital,
        especialidad=horario.especialidad,
        fecha_hora__gt=horario.fecha_hora,
        estado__in=[
            Cita.Estado.PENDIENTE,
            Cita.Estado.CONFIRMADA,
        ],
    ).order_by("fecha_solicitud").first()

    mensaje = (
        f"Tienes una oferta de horario para el "
        f"{fecha_nueva:%d/%m/%Y a las %H:%M}. "
        f"Hospital: {horario.hospital.nombre}. "
        f"Especialidad: {horario.especialidad.nombre}."
    )

    if cita_actual:
        fecha_actual = timezone.localtime(cita_actual.fecha_hora)

        mensaje += (
            f" Tu cita actual es el "
            f"{fecha_actual:%d/%m/%Y a las %H:%M}, "
            f"en {cita_actual.hospital.nombre}, "
            f"especialidad {cita_actual.especialidad.nombre}."
        )

    mensaje += (
        " Ingresa a CitaHN para aceptar o rechazar la oferta."
    )

    return Notificacion.objects.create(
        usuario=oferta.paciente,
        tipo=Notificacion.Tipo.OFERTA,
        canal=Notificacion.Canal.EMAIL,
        mensaje=mensaje,
        enviada=False,
        oferta_cita=oferta,
    )
