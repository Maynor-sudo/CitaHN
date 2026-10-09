
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.medicos.models import Medico, Disponibilidad


class Command(BaseCommand):
    help = "Asigna horarios semanales sin duplicar días existentes."

    DIAS_LABORALES = [0, 1, 2, 3, 4]
    SABADO = 5
    DOMINGO = 6

    HORA_INICIO = "08:00"
    HORA_FIN = "16:00"
    HORA_FIN_SABADO = "12:00"
    HORA_FIN_DOMINGO = "12:00"

    ESPECIALIDADES_CRITICAS = {
        "Cardiología",
        "Cardiología Pediátrica",
        "Cardiología Intervencionista",
        "Cirugía General",
        "Cirugía Cardiovascular",
        "Cirugía Cardiovascular Pediátrica",
        "Cirugía Torácica",
        "Ginecología y Obstetricia",
        "Medicina Interna",
        "Neumología",
        "Neumología Pediátrica",
        "Pediatría",
        "Psiquiatría",
    }

    def handle(self, *args, **options):
        medicos = list(
            Medico.objects.filter(activo=True)
            .select_related("usuario", "hospital", "especialidad")
            .order_by(
                "hospital__nombre",
                "especialidad__nombre",
                "numero_colegiacion",
            )
        )

        grupos = defaultdict(list)

        for medico in medicos:
            clave = (medico.hospital_id, medico.especialidad_id)
            grupos[clave].append(medico)

        # Un médico por hospital y especialidad crítica cubrirá el domingo.
        medicos_domingo = set()

        for grupo in grupos.values():
            if grupo[0].especialidad.nombre in self.ESPECIALIDADES_CRITICAS:
                medicos_domingo.add(grupo[0].id)

        creados = 0
        conservados = 0
        desactivados = 0

        with transaction.atomic():
            for medico in medicos:
                trabaja_domingo = medico.id in medicos_domingo

                if trabaja_domingo:
                    # Descanso semanal: miércoles y sábado.
                    dias_deseados = [0, 1, 3, 4, 6]
                    dias_descanso = [2, 5]
                else:
                    # Horario ambulatorio habitual.
                    dias_deseados = [0, 1, 2, 3, 4, 5]
                    dias_descanso = [6]

                # Desactivar los días de descanso del médico dominical.
                for dia in dias_descanso:
                    if trabaja_domingo:
                        desactivados += Disponibilidad.objects.filter(
                            medico=medico,
                            dia_semana=dia,
                            activo=True,
                        ).update(activo=False)

                for dia in dias_deseados:
                    existentes = Disponibilidad.objects.filter(
                        medico=medico,
                        dia_semana=dia,
                    )

                    if existentes.exists():
                        conservados += 1
                        continue

                    hora_inicio = self.HORA_INICIO

                    if dia == self.SABADO:
                        hora_fin = self.HORA_FIN_SABADO
                    elif dia == self.DOMINGO:
                        hora_fin = self.HORA_FIN_DOMINGO
                    else:
                        hora_fin = self.HORA_FIN

                    Disponibilidad.objects.create(
                        medico=medico,
                        dia_semana=dia,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        activo=True,
                    )
                    creados += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Proceso terminado.\n"
                f"Médicos revisados: {len(medicos)}\n"
                f"Horarios creados: {creados}\n"
                f"Días con registros existentes conservados: "
                f"{conservados}\n"
                f"Horarios desactivados para descanso: {desactivados}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                "Importante: esta configuración es una propuesta "
                "para datos de prueba. No sustituye los turnos "
                "oficiales ni garantiza cobertura de urgencias."
            )
        )
