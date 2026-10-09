
from datetime import date
from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea 5 usuarios médicos adicionales."

    def handle(self, *args, **options):
        nombres = [
            ("José", "Hernández"),
            ("María", "Martínez"),
            ("Carlos", "López"),
            ("Ana", "García"),
            ("Daniel", "Flores"),
        ]

        creados = 0

        for i, (nombre, apellido) in enumerate(nombres):
            dni = str(202110010686 + i)

            if Usuario.objects.filter(identidad=dni).exists():
                self.stderr.write(f"Ya existe el DNI {dni}.")
                continue

            Usuario.objects.create_user(
                identidad=dni,
                password="Medico123!",
                nombre=nombre,
                apellido=apellido,
                email=f"medico{dni}@example.com",
                telefono=f"98{dni[-6:]}",
                fecha_nacimiento=date(1990, 1, 15),
                rol=Usuario.Rol.MEDICO,
                activo=True,
                is_staff=False,
            )

            creados += 1
            self.stdout.write(f"Creado: {dni} | {nombre} {apellido}")

        self.stdout.write(
            self.style.SUCCESS(f"Usuarios creados: {creados}")
        )
