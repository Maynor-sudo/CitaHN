
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.hospitales.models import Hospital, Especialidad
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Asigna 5 médicos al Hospital Tela Integrado."

    def handle(self, *args, **options):
        distribucion = [
            ("Medicina General", 2),
            ("Pediatría", 1),
            ("Ginecología y Obstetricia", 1),
            ("Cirugía General", 1),
        ]

        with transaction.atomic():
            hospital = Hospital.objects.filter(
                nombre__iexact="Hospital Tela Integrado",
                activo=True,
            ).first()

            if not hospital:
                raise CommandError(
                    "No se encontró el Hospital Tela Integrado activo."
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
                        f"{nombre} no está asociada al Hospital Tela Integrado."
                    )

                asignaciones.extend([especialidad] * cantidad)

            usuarios = list(
                Usuario.objects.filter(
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    perfil_medico__isnull=True,
                ).order_by("identidad")[:5]
            )

            if len(usuarios) < 5:
                raise CommandError(
                    f"Solo hay {len(usuarios)} usuarios disponibles. "
                    "No se realizaron asignaciones."
                )

            numeros = [
                f"MED-{n:03d}"
                for n in range(31, 36)
            ]

            if Medico.objects.filter(
                numero_colegiacion__in=numeros
            ).exists():
                raise CommandError(
                    "Alguno de los números MED-031 a MED-035 ya existe. "
                    "No se realizaron asignaciones."
                )

            for usuario, especialidad, numero in zip(
                usuarios, asignaciones, numeros
            ):
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
                "Se asignaron correctamente 5 médicos al Hospital Tela Integrado."
            )
        )
