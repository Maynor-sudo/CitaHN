
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.hospitales.models import Hospital, Especialidad
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Asigna 7 médicos al Hospital Regional de Atlántida."

    def handle(self, *args, **options):
        distribucion = [
            ("Medicina General", 2),
            ("Medicina Interna", 1),
            ("Pediatría", 1),
            ("Ginecología y Obstetricia", 1),
            ("Cirugía General", 1),
            ("Ortopedia", 1),
        ]

        with transaction.atomic():
            hospital = Hospital.objects.filter(
                nombre__iexact="Hospital Regional de Atlántida",
                activo=True,
            ).first()

            if not hospital:
                raise CommandError(
                    "No se encontró el Hospital Regional de Atlántida activo."
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
                        f"{nombre} no está asociada a este hospital."
                    )

                asignaciones.extend([especialidad] * cantidad)

            usuarios = list(
                Usuario.objects.filter(
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    perfil_medico__isnull=True,
                ).order_by("identidad")[:7]
            )

            if len(usuarios) < 7:
                raise CommandError(
                    f"Solo hay {len(usuarios)} usuarios disponibles. "
                    "No se realizaron asignaciones."
                )

            numeros = [
                f"MED-{n:03d}"
                for n in range(24, 31)
            ]

            if Medico.objects.filter(
                numero_colegiacion__in=numeros
            ).exists():
                raise CommandError(
                    "Alguno de los números MED-024 a MED-030 ya existe. "
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
                "Se asignaron correctamente 7 médicos al Hospital Regional de Atlántida."
            )
        )
