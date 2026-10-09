
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.hospitales.models import Hospital, Especialidad
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Asigna 11 médicos al Hospital Escuela."

    def handle(self, *args, **options):
        distribucion = [
            ("Medicina General", 2),
            ("Medicina Interna", 2),
            ("Pediatría", 2),
            ("Cardiología", 1),
            ("Cirugía General", 1),
            ("Ortopedia", 1),
            ("Ginecología y Obstetricia", 1),
            ("Odontología", 1),
        ]

        with transaction.atomic():
            hospital = Hospital.objects.filter(
                nombre__iexact="Hospital Escuela",
                activo=True,
            ).first()

            if not hospital:
                raise CommandError(
                    "No se encontró el Hospital Escuela activo."
                )

            asignaciones = []

            for nombre, cantidad in distribucion:
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
                        f"{nombre} no está asociada al Hospital Escuela."
                    )

                asignaciones.extend([especialidad] * cantidad)

            usuarios = list(
                Usuario.objects.filter(
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    perfil_medico__isnull=True,
                ).order_by("identidad")[:11]
            )

            if len(usuarios) < 11:
                raise CommandError(
                    f"Solo hay {len(usuarios)} usuarios médicos "
                    "disponibles. No se realizaron asignaciones."
                )

            for indice, (usuario, especialidad) in enumerate(
                zip(usuarios, asignaciones),
                start=1,
            ):
                numero = f"PRUEBA-HE-{indice:03d}"

                if Medico.objects.filter(
                    numero_colegiacion=numero
                ).exists():
                    raise CommandError(
                        f"El número {numero} ya existe. "
                        "No se realizaron asignaciones."
                    )

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

        self.stdout.write(
            self.style.SUCCESS(
                "Se asignaron correctamente 11 médicos al Hospital Escuela."
            )
        )
