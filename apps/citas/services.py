from datetime import datetime, timedelta
from django.utils import timezone

from apps.citas.models import Cita, OfertaCita, HorarioLiberado
from apps.medicos.models import BloqueoHorario
from django.db import IntegrityError, transaction
from apps.notificaciones.services import notificar_oferta_cita

DURACION_CITA = timedelta(minutes=20)


def generar_slots(disponibilidad, fecha):
    inicio = timezone.make_aware(datetime.combine(fecha, disponibilidad.hora_inicio))

    fin = timezone.make_aware(datetime.combine(fecha, disponibilidad.hora_fin))

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

    citas_ocupadas = {cita.fecha_hora for cita in citas}

    bloqueos = BloqueoHorario.objects.filter(
        medico=medico,
        inicio__date__lte=fecha,
        fin__date__gte=fecha,
    )

    ahora = timezone.now()

    slots_disponibles = []

    for slot in slots:
        slot_fin = slot + DURACION_CITA

        # Nunca mostrar un horario que ya comenzó.
        if slot <= ahora:
            continue

        ocupado = slot in citas_ocupadas

        bloqueado = any(
            slot < bloqueo.fin and slot_fin > bloqueo.inicio for bloqueo in bloqueos
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

    medicos_rotacion = medicos[inicio_rotacion:] + medicos[:inicio_rotacion]

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

                    if slot >= timezone.make_aware(
                        datetime.combine(fecha_inicio, datetime.min.time())
                    ):
                        return slot

        fecha += timedelta(days=1)

    return None


def obtener_horarios_disponibles(especialidad, hospital, fecha):
    horarios = []

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

                if slot not in horarios:
                    horarios.append(slot)

    return sorted(horarios)


@transaction.atomic
def crear_cita(paciente, especialidad, hospital, fecha_hora, motivo):
    medico = asignar_medico(especialidad, hospital, fecha_hora)

    if medico is None:
        return None

    try:
        cita = Cita.objects.create(
            paciente=paciente,
            medico=medico,
            hospital=hospital,
            especialidad=especialidad,
            fecha_hora=fecha_hora,
            motivo=motivo,
            estado=Cita.Estado.CONFIRMADA,
        )
    except IntegrityError:
        # Otro usuario pudo reservar el mismo horario.
        return None

    return cita


@transaction.atomic
def cancelar_cita(cita):
    ahora = timezone.now()
    limite = cita.fecha_hora - timedelta(hours=12)

    if ahora > limite:
        return False

    cita.estado = Cita.Estado.CANCELADA

    cita.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )

    horario_liberado = HorarioLiberado.objects.create(
        hospital=cita.hospital,
        especialidad=cita.especialidad,
        medico=cita.medico,
        fecha_hora=cita.fecha_hora,
    )

    crear_oferta_siguiente(horario_liberado)

    return True


def buscar_candidatos_oferta(horario_liberado):

    ahora = timezone.now()

    limite_48_horas = ahora + timedelta(hours=48)

    candidatos = (
        Cita.objects.filter(
            especialidad=horario_liberado.especialidad,
            hospital=horario_liberado.hospital,
            fecha_hora__gt=horario_liberado.fecha_hora,
            fecha_hora__gte=limite_48_horas,
            estado__in=[
                Cita.Estado.PENDIENTE,
                Cita.Estado.CONFIRMADA,
            ],
        )
        .exclude(
            paciente__in=OfertaCita.objects.filter(
                horario_liberado=horario_liberado
            ).values("paciente")
        )
        .order_by("fecha_solicitud")[:2]
    )

    return candidatos


def crear_oferta_siguiente(horario_liberado):

    if not horario_liberado.disponible:
        return None

    ofertas_realizadas = OfertaCita.objects.filter(
        horario_liberado=horario_liberado
    ).count()

    if ofertas_realizadas >= 2:
        return None

    candidato = buscar_candidatos_oferta(horario_liberado).first()

    if not candidato:
        return None

    oferta = OfertaCita.objects.create(
        horario_liberado=horario_liberado,
        paciente=candidato.paciente,
    )

    notificar_oferta_cita(oferta)

    return oferta




@transaction.atomic
def aceptar_oferta(oferta):
    print("PASO 0: iniciando aceptación")

    if oferta.aceptada is not None:
        print("FALLO: oferta ya procesada")
        return False

    horario_nuevo = oferta.horario_liberado

    if horario_nuevo is None or not horario_nuevo.disponible:
        print("FALLO: horario inexistente o no disponible")
        return False

    print("PASO 1: horario validado")

    cita_actual = (
        Cita.objects.select_for_update()
        .filter(
            paciente=oferta.paciente,
            especialidad=horario_nuevo.especialidad,
            hospital=horario_nuevo.hospital,
            fecha_hora__gt=horario_nuevo.fecha_hora,
            fecha_hora__gte=timezone.now() + timedelta(hours=48),
            estado__in=[
                Cita.Estado.PENDIENTE,
                Cita.Estado.CONFIRMADA,
            ],
        )
        .order_by("fecha_solicitud")
        .first()
    )

    if not cita_actual:
        print("FALLO: no se encontró cita candidata")
        return False

    print("PASO 2: cita encontrada", cita_actual.id)

    medico_nuevo = asignar_medico(
        horario_nuevo.especialidad,
        horario_nuevo.hospital,
        horario_nuevo.fecha_hora,
    )

    if medico_nuevo is None:
        print("FALLO: no hay médico disponible")
        return False

    print("PASO 3: médico asignado", medico_nuevo.id)

    fecha_anterior = cita_actual.fecha_hora
    medico_anterior = cita_actual.medico

    try:
        with transaction.atomic():
            cita_actual.fecha_hora = horario_nuevo.fecha_hora
            cita_actual.medico = medico_nuevo
            cita_actual.estado = Cita.Estado.CONFIRMADA

            cita_actual.save(
                update_fields=[
                    "fecha_hora",
                    "medico",
                    "estado",
                    "fecha_actualizacion",
                ]
            )
    except IntegrityError as error:
        print("ERROR DE INTEGRIDAD:", error)
        return False

    print("PASO 4: cita guardada")

    horario_nuevo.disponible = False
    horario_nuevo.save(update_fields=["disponible"])

    oferta.aceptada = True
    oferta.save(update_fields=["aceptada"])

    horario_anterior = HorarioLiberado.objects.create(
        hospital=cita_actual.hospital,
        especialidad=cita_actual.especialidad,
        medico=medico_anterior,
        fecha_hora=fecha_anterior,
    )

    crear_oferta_siguiente(horario_anterior)

    print("PASO 5: oferta aceptada correctamente")
    return True




def rechazar_oferta(oferta):

    if oferta.aceptada is not None:
        return False

    oferta.aceptada = False

    oferta.save(update_fields=["aceptada"])

    crear_oferta_siguiente(oferta.horario_liberado)

    return True
