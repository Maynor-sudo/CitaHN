from datetime import datetime, timedelta

from django.utils import timezone

from apps.citas.models import Cita
from apps.medicos.models import BloqueoHorario


DURACION_CITA = timedelta(minutes=20)


def generar_slots(disponibilidad, fecha):
    inicio = timezone.make_aware(
        datetime.combine(fecha, disponibilidad.hora_inicio)
    )

    fin = timezone.make_aware(
        datetime.combine(fecha, disponibilidad.hora_fin)
    )

    slots = []
    actual = inicio

    while actual + DURACION_CITA <= fin:
        slots.append(actual)
        actual += DURACION_CITA

    return slots


def obtener_slots_disponibles(medico, disponibilidad, fecha):
    slots = generar_slots(disponibilidad, fecha)

    citas = Cita.objects.filter(
        medico=medico,
        fecha_hora__date=fecha,
        estado__in=[
            Cita.Estado.PENDIENTE,
            Cita.Estado.CONFIRMADA,
        ],
    )

    citas_ocupadas = {
        cita.fecha_hora
        for cita in citas
    }

    bloqueos = BloqueoHorario.objects.filter(
        medico=medico,
        inicio__date__lte=fecha,
        fin__date__gte=fecha,
    )

    slots_disponibles = []

    for slot in slots:
        slot_fin = slot + DURACION_CITA

        ocupado = slot in citas_ocupadas

        bloqueado = any(
            slot < bloqueo.fin and slot_fin > bloqueo.inicio
            for bloqueo in bloqueos
        )

        if not ocupado and not bloqueado:
            slots_disponibles.append(slot)

    return slots_disponibles

def asignar_medico(especialidad, hospital, fecha_hora):
    medicos = list(
        especialidad.medicos.filter(
            hospital=hospital,
            activo=True,
            usuario__activo=True,
        ).order_by("id")
    )

    if not medicos:
        return None

    citas_del_dia = Cita.objects.filter(
        hospital=hospital,
        especialidad=especialidad,
        fecha_hora__date=fecha_hora.date(),
        estado__in=[
            Cita.Estado.PENDIENTE,
            Cita.Estado.CONFIRMADA,
        ],
    ).order_by("fecha_hora")

    cantidad_asignaciones = citas_del_dia.count()

    inicio_rotacion = cantidad_asignaciones % len(medicos)

    medicos_rotacion = (
        medicos[inicio_rotacion:]
        + medicos[:inicio_rotacion]
    )

    for medico in medicos_rotacion:
        disponibilidad = medico.disponibilidades.filter(
            dia_semana=fecha_hora.weekday(),
            activo=True,
            hora_inicio__lte=fecha_hora.time(),
            hora_fin__gte=(fecha_hora + DURACION_CITA).time(),
        ).first()

        if not disponibilidad:
            continue

        bloqueo = BloqueoHorario.objects.filter(
            medico=medico,
            inicio__lt=fecha_hora + DURACION_CITA,
            fin__gt=fecha_hora,
        ).exists()

        if bloqueo:
            continue

        ocupado = Cita.objects.filter(
            medico=medico,
            fecha_hora=fecha_hora,
            estado__in=[
                Cita.Estado.PENDIENTE,
                Cita.Estado.CONFIRMADA,
            ],
        ).exists()

        if not ocupado:
            return medico
    return None
def buscar_siguiente_slot(especialidad, hospital, fecha_inicio, dias_maximos=30):
    fecha = fecha_inicio

    for _ in range(dias_maximos):
        medicos = especialidad.medicos.filter(
            hospital=hospital,
            activo=True,
            usuario__activo=True,
        )

        for medico in medicos:
            disponibilidades = medico.disponibilidades.filter(
                dia_semana=fecha.weekday(),
                activo=True,
            )

            for disponibilidad in disponibilidades:
                slots = obtener_slots_disponibles(
                    medico,
                    disponibilidad,
                    fecha,
                )

                for slot in slots:
                    if slot >= fecha_inicio:
                        return slot

        fecha += timedelta(days=1)

    return None

from django.db import transaction


@transaction.atomic
def crear_cita(paciente, especialidad, hospital, fecha_hora, motivo):
    medico = asignar_medico(
        especialidad,
        hospital,
        fecha_hora
    )

    if medico is None:
        return None

    cita = Cita.objects.create(
        paciente=paciente,
        medico=medico,
        hospital=hospital,
        especialidad=especialidad,
        fecha_hora=fecha_hora,
        motivo=motivo,
        estado=Cita.Estado.CONFIRMADA,
    )

    return cita

from django.utils import timezone


def cancelar_cita(cita):
    ahora = timezone.now()
    limite = cita.fecha_hora - timedelta(hours=12)

    if ahora > limite:
        return False

    cita.estado = Cita.Estado.CANCELADA
    cita.save(update_fields=["estado", "fecha_actualizacion"])

    return True

def buscar_candidatos_oferta(cita_liberada):
    ahora = timezone.now()
    limite_48_horas = ahora + timedelta(hours=48)

    candidatos = Cita.objects.filter(
        especialidad=cita_liberada.especialidad,
        hospital=cita_liberada.hospital,
        fecha_hora__gt=cita_liberada.fecha_hora,
        fecha_hora__gte=limite_48_horas,
        estado__in=[
            Cita.Estado.PENDIENTE,
            Cita.Estado.CONFIRMADA,
        ],
    ).exclude(
        paciente__in=OfertaCita.objects.filter(
            cita_origen=cita_liberada
        ).values("paciente")
    ).order_by(
        "fecha_solicitud"
    )[:2]

    return candidatos

def crear_oferta_siguiente(cita_liberada):
    ofertas_realizadas = OfertaCita.objects.filter(
        cita_origen=cita_liberada
    ).count()

    if ofertas_realizadas >= 2:
        return None

    candidato = buscar_candidatos_oferta(cita_liberada).first()

    if not candidato:
        return None

    return OfertaCita.objects.create(
        cita_origen=cita_liberada,
        paciente=candidato.paciente,
    )


@transaction.atomic
def aceptar_oferta(oferta):
    if oferta.aceptada is not None:
        return False

    cita_nueva = oferta.cita_origen
    cita_actual = Cita.objects.filter(
        paciente=oferta.paciente,
        especialidad=cita_nueva.especialidad,
        hospital=cita_nueva.hospital,
        fecha_hora__gt=cita_nueva.fecha_hora,
        estado__in=[
            Cita.Estado.PENDIENTE,
            Cita.Estado.CONFIRMADA,
        ],
    ).order_by("fecha_solicitud").first()

    if not cita_actual:
        oferta.aceptada = False
        oferta.save(update_fields=["aceptada"])
        return False

    medico = asignar_medico(
        cita_nueva.especialidad,
        cita_nueva.hospital,
        cita_nueva.fecha_hora,
    )

    if medico is None:
        return False

    cita_actual.fecha_hora = cita_nueva.fecha_hora
    cita_actual.medico = medico
    cita_actual.estado = Cita.Estado.CONFIRMADA
    cita_actual.save(
        update_fields=["fecha_hora", "medico", "estado", "fecha_actualizacion"]
    )

    oferta.aceptada = True
    oferta.save(update_fields=["aceptada"])

    return True


def rechazar_oferta(oferta):
    if oferta.aceptada is not None:
        return False

    oferta.aceptada = False
    oferta.save(update_fields=["aceptada"])

    crear_oferta_siguiente(oferta.cita_origen)

    return True