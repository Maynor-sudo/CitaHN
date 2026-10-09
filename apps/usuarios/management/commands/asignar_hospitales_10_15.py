
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.hospitales.models import Hospital, Especialidad
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Asigna médicos a los hospitales 10 al 15."

    DISTRIBUCION = [
        {
            "hospital": "Hospital de Puerto Cortés",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "hospital": "Hospital General del Sur",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Cardiología", 1),
                ("Cirugía General", 1),
                ("Ortopedia", 1),
            ],
        },
        {
            "hospital": "Hospital Gabriela Alvarado",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "hospital": "Hospital San Felipe",
            "especialidades": [
                ("Medicina General", 1),
                ("Medicina Interna", 1),
                ("Cardiología", 1),
                ("Pediatría", 1),
                ("Cirugía General", 1),
                ("Ortopedia", 1),
                ("Ginecología y Obstetricia", 1),
                ("Odontología", 1),
            ],
        },
        {
            "hospital": "Hospital Nacional del Tórax",
            "especialidades": [
                ("Cardiología", 1),
                ("Cirugía Torácica", 1),
                ("Hemato-Oncología", 1),
                ("Medicina Interna", 1),
                ("Neumología", 1),
                ("Neumología Pediátrica", 1),
            ],
        },
        {
            "hospital": "Hospital Psiquiátrico Mario Mendoza",
            "especialidades": [
                ("Psiquiatría", 2),
                ("Psicología", 2),
            ],
        },
    ]

    def handle(self, *args, **options):
        with transaction.atomic():
            plan = []

            # Validar hospitales y especialidades.
            for item in self.DISTRIBUCION:
                hospital = Hospital.objects.filter(
                    nombre__iexact=item["hospital"],
                    activo=True,
                ).first()

                if not hospital:
                    raise CommandError(
                        f"No se encontró el hospital: {item['hospital']}"
                    )

                asignaciones = []

                for nombre, cantidad in item["especialidades"]:
                    especialidad = Especialidad.objects.filter(
                        nombre__iexact=nombre,
                        activo=True,
                    ).first()

                    if not especialidad:
                        raise CommandError(
                            f"No existe la especialidad: {nombre}"
                        )

                    if not hospital.especialidades.filter(
                        pk=especialidad.pk
                    ).exists():
                        raise CommandError(
                            f"{nombre} no está asociada a "
                            f"{hospital.nombre}."
                        )

                    asignaciones.extend([especialidad] * cantidad)

                plan.append((hospital, asignaciones))

            total = sum(
                len(asignaciones)
                for _, asignaciones in plan
            )

            usuarios = list(
                Usuario.objects.filter(
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    perfil_medico__isnull=True,
                ).order_by("identidad")[:total]
            )

            if len(usuarios) < total:
                raise CommandError(
                    f"Se necesitan {total} usuarios disponibles, "
                    f"pero solo hay {len(usuarios)}. No se guardó nada."
                )

            numeros = [
                f"MED-{n:03d}"
                for n in range(70, 70 + total)
            ]

            if Medico.objects.filter(
                numero_colegiacion__in=numeros
            ).exists():
                raise CommandError(
                    "Ya existe alguna colegiación desde MED-070. "
                    "No se guardó ninguna asignación."
                )

            indice = 0

            for hospital, asignaciones in plan:
                self.stdout.write(f"\n{hospital.nombre}")

                for especialidad in asignaciones:
                    usuario = usuarios[indice]
                    numero = numeros[indice]

                    Medico.objects.create(
                        usuario=usuario,
                        hospital=hospital,
                        especialidad=especialidad,
                        numero_colegiacion=numero,
                        activo=True,
                    )

                    self.stdout.write(
                        f"{usuario.identidad} | "
                        f"{usuario.nombre} {usuario.apellido} | "
                        f"{especialidad.nombre} | {numero}"
                    )

                    indice += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSe asignaron {indice} médicos correctamente."
            )
        )
