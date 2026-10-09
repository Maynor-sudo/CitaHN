
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.hospitales.models import Hospital, Especialidad
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Asigna médicos a los hospitales 5 al 9 de CitaHN."

    DISTRIBUCION = [
        {
            "hospital": "Hospital Salvador Paredes",
            "cantidad": 6,
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "hospital": "Hospital San Isidro",
            "cantidad": 6,
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "hospital": "Hospital Santa Teresa",
            "cantidad": 6,
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Ortopedia", 1),
            ],
        },
        {
            "hospital": "Hospital Regional de Occidente",
            "cantidad": 7,
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
            "hospital": "Hospital Leonardo Martínez Valenzuela",
            "cantidad": 9,
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 2),
                ("Ginecología y Obstetricia", 2),
                ("Cirugía General", 1),
                ("Ortopedia", 1),
            ],
        },
    ]

    def handle(self, *args, **options):
        with transaction.atomic():
            plan = []

            # Validar todos los hospitales y especialidades antes de crear.
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

                if len(asignaciones) != item["cantidad"]:
                    raise CommandError(
                        f"La distribución de {hospital.nombre} "
                        "no coincide con la cantidad indicada."
                    )

                plan.append((hospital, asignaciones))

            total = sum(item["cantidad"] for item in self.DISTRIBUCION)

            usuarios = list(
                Usuario.objects.filter(
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    perfil_medico__isnull=True,
                ).order_by("identidad")[:total]
            )

            if len(usuarios) < total:
                raise CommandError(
                    f"Se necesitan {total} usuarios médicos disponibles, "
                    f"pero solo hay {len(usuarios)}. No se guardó nada."
                )

            numeros = [
                f"MED-{n:03d}"
                for n in range(36, 36 + total)
            ]

            if Medico.objects.filter(
                numero_colegiacion__in=numeros
            ).exists():
                raise CommandError(
                    "Ya existe uno de los números de colegiación "
                    "MED-036 en adelante. No se guardó nada."
                )

            indice_usuario = 0
            indice_numero = 0

            for hospital, asignaciones in plan:
                self.stdout.write(f"\n{hospital.nombre}")

                for especialidad in asignaciones:
                    usuario = usuarios[indice_usuario]
                    numero = numeros[indice_numero]

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

                    indice_usuario += 1
                    indice_numero += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSe asignaron {indice_numero} médicos "
                "a los cinco hospitales correctamente."
            )
        )
