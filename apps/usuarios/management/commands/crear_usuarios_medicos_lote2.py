
import random
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea 59 usuarios médicos ficticios para CitaHN."

    def handle(self, *args, **options):
        cantidad = 59
        dni_inicial = 202110010627
        contrasena = "Medico123!"

        nombres = [
            "María José", "Ana", "Gabriela", "Daniela", "Valeria",
            "Sofía", "Camila", "Fernanda", "Andrea", "Isabella",
            "Karla", "Claudia", "Patricia", "Alejandra", "Lucía",
            "Paola", "Melissa", "Natalia", "Adriana", "Verónica",
            "Mónica", "Carolina", "Rebeca", "Mariana", "Diana",
            "Irene", "Silvia", "Teresa", "Rosa", "Elena",
            "Carlos", "Luis", "José", "Miguel", "Andrés",
            "Daniel", "Jorge", "David", "Fernando", "Ricardo",
            "Óscar", "Mario", "Eduardo", "Roberto", "Sergio",
            "Alejandro", "Gabriel", "Rafael", "Héctor", "Francisco",
            "Pedro", "Marco", "Víctor", "Adrián", "César",
            "Javier", "Mauricio", "Esteban", "Samuel",
        ]

        apellidos = [
            "Hernández", "Martínez", "López", "García",
            "Rodríguez", "Pérez", "Sánchez", "Ramírez",
            "Flores", "Gómez", "Cruz", "Reyes", "Díaz",
            "Castillo", "Mejía", "Rivera", "Aguilar",
            "Mendoza", "Vásquez", "Romero", "Ortiz",
            "Morales", "Gutiérrez", "Chávez", "Pineda",
            "Alvarado", "Suárez", "Figueroa", "Cáceres",
            "Banegas", "Zelaya", "Amador", "Espinoza",
            "Molina", "Salgado", "Perdomo", "Cálix",
            "Orellana", "Turcios", "Portillo", "Sabillón",
            "Bautista", "Navarro", "Varela", "Barahona",
            "Cerrato", "Andino", "Bonilla", "Sierra",
            "Valle", "Paz", "Lagos", "Méndez", "Duarte",
            "Osorio", "Escobar", "Montoya", "Caballero",
            "Murillo",
        ]

        creados = 0

        with transaction.atomic():
            telefonos_usados = set(
                Usuario.objects.values_list("telefono", flat=True)
            )

            for i in range(cantidad):
                identidad = str(dni_inicial + i)

                if Usuario.objects.filter(
                    identidad=identidad
                ).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ya existe el DNI {identidad}; se cancela el proceso."
                        )
                    )
                    raise CommandError(
                        "Se encontró un DNI existente. No se creó ningún usuario."
                    )

                nombre = nombres[i]
                apellido = apellidos[i]

                correo = f"medico{identidad}@example.com"

                while True:
                    telefono = str(random.randint(90000000, 99999999))
                    if telefono not in telefonos_usados:
                        telefonos_usados.add(telefono)
                        break

                anio = random.randint(1975, 2000)
                mes = random.randint(1, 12)
                dia = random.randint(1, 28)

                Usuario.objects.create_user(
                    identidad=identidad,
                    password=contrasena,
                    nombre=nombre,
                    apellido=apellido,
                    email=correo,
                    telefono=telefono,
                    fecha_nacimiento=date(anio, mes, dia),
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    is_staff=False,
                )

                creados += 1
                self.stdout.write(
                    f"Creado: {identidad} | {nombre} {apellido}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso terminado: {creados} usuarios creados."
            )
        )
        self.stdout.write(
            f"DNI inicial: {dni_inicial} | "
            f"DNI final: {dni_inicial + cantidad - 1}"
        )
        self.stdout.write(
            f"Contraseña inicial: {contrasena}"
        )


from django.core.management.base import CommandError
