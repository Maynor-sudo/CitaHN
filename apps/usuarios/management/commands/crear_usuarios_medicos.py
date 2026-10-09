
import random
from datetime import date

from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea usuarios ficticios para médicos de CitaHN."

    def handle(self, *args, **options):
        cantidad = 74
        dni_inicial = 202110010553
        contrasena = "Medico123!"

        nombres = [
            "Carlos", "Luis", "José", "Miguel", "Andrés",
            "Daniel", "Jorge", "David", "Fernando", "Ricardo",
            "Óscar", "Mario", "Eduardo", "Roberto", "Sergio",
            "Alejandro", "Gabriel", "Rafael", "Héctor", "Francisco",
            "Pedro", "Marco", "Víctor", "Adrián", "César",
            "Kevin", "Christian", "Javier", "Mauricio", "Esteban",
            "Raúl", "Tomás", "Samuel", "Isaac", "Ángel",
            "Diego", "Emilio", "Alberto", "Manuel", "Pablo",
            "Julio", "Erick", "Noel", "Wilmer", "Bryan",
            "Allan", "Saúl", "René", "Abraham", "Jonathan",
            "Gustavo", "Leonel", "Benjamín", "Rubén", "Damián",
            "Marvin", "Franklin", "Cristian", "Orlando", "Arnold",
            "Iván", "Joel", "Emanuel", "Matías", "Fabián",
            "Rodrigo", "Axel", "Nicolás", "Alexis", "Elías",
            "Gerardo", "Walter", "Amílcar", "Dylan",
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
            "Murillo", "Ramos", "Arias", "Leiva", "Bueso",
            "Matute", "Pavón", "Zúniga", "Dubón", "Ponce",
            "Córdova", "Coto",
        ]

        creados = 0
        existentes = 0

        telefonos_usados = set(
            Usuario.objects.values_list("telefono", flat=True)
        )

        for i in range(cantidad):
            identidad = str(dni_inicial + i)

            if Usuario.objects.filter(identidad=identidad).exists():
                existentes += 1
                continue

            nombre = nombres[i % len(nombres)]
            apellido = apellidos[i % len(apellidos)]
            correo = f"medico{identidad}@example.com"

            while True:
                telefono = str(random.randint(90000000, 99999999))
                if telefono not in telefonos_usados:
                    telefonos_usados.add(telefono)
                    break

            anio = random.randint(1975, 2000)
            mes = random.randint(1, 12)
            dia = random.randint(1, 28)
            nacimiento = date(anio, mes, dia)

            usuario = Usuario.objects.create_user(
                identidad=identidad,
                password=contrasena,
                nombre=nombre,
                apellido=apellido,
                email=correo,
                telefono=telefono,
                fecha_nacimiento=nacimiento,
                rol=Usuario.Rol.MEDICO,
                activo=True,
                is_staff=False,
            )

            creados += 1
            self.stdout.write(
                f"Creado: {usuario.nombre} {usuario.apellido} "
                f"| DNI: {identidad} | {correo} | {telefono}"
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso terminado. Creados: {creados}. "
                f"Omitidos por DNI existente: {existentes}."
            )
        )
        self.stdout.write(
            f"Contraseña inicial: {contrasena}"
        )
