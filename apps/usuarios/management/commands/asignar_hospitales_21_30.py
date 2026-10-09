
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.hospitales.models import Hospital, Especialidad
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Crea usuarios y asigna médicos a los hospitales 21 al 30."

    HOSPITALES = [
        {
            "nombre": "Hospital Juan Manuel Gálvez",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital de San Marcos",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital San Francisco",
            "especialidades": [
                ("Medicina General", 2),
                ("Cardiología", 1),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
            ],
        },
        {
            "nombre": "Hospital Santo Hermano Pedro",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital Santa Bárbara Integrado",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital San Lorenzo",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Psicología", 1),
            ],
        },
        {
            "nombre": "Hospital El Progreso",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital Manuel J. Subirana",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital Aníbal Murillo",
            "especialidades": [
                ("Cirugía General", 2),
                ("Ginecología y Obstetricia", 2),
            ],
        },
        {
            "nombre": "Hospital Psiquiátrico Santa Rosita",
            "especialidades": [
                ("Psiquiatría", 2),
                ("Psicología", 2),
            ],
        },
    ]

    NOMBRES = [
        "José", "María", "Carlos", "Ana", "Daniel", "Gabriela",
        "Luis", "Sofía", "Miguel", "Valeria", "Andrés", "Lucía",
        "Jorge", "Camila", "David", "Fernanda", "Mario", "Paola",
        "Ricardo", "Andrea", "Pedro", "Natalia", "Fernando",
        "Claudia", "Eduardo", "Isabella", "Roberto", "Diana",
        "Alejandro", "Karla", "Javier", "Rebeca", "Óscar",
        "Melissa", "Rafael", "Adriana", "Samuel", "Elena",
        "César", "Daniela", "Marco", "Patricia", "Héctor",
        "Mariana", "Sergio", "Teresa", "Francisco", "Irene",
        "Mauricio", "Carolina", "Víctor", "Silvia", "Esteban",
        "Rosa", "Gabriel", "Mónica", "Adrián",
    ]

    APELLIDOS = [
        "Hernández", "Martínez", "López", "García", "Rodríguez",
        "Pérez", "Sánchez", "Ramírez", "Flores", "Gómez",
        "Cruz", "Reyes", "Díaz", "Castillo", "Mejía", "Rivera",
        "Aguilar", "Mendoza", "Vásquez", "Romero", "Ortiz",
        "Morales", "Gutiérrez", "Chávez", "Pineda", "Alvarado",
        "Suárez", "Figueroa", "Cáceres", "Banegas", "Zelaya",
        "Amador", "Espinoza", "Molina", "Salgado", "Perdomo",
        "Cálix", "Orellana", "Turcios", "Portillo", "Sabillón",
        "Bautista", "Navarro", "Varela", "Barahona", "Cerrato",
        "Andino", "Bonilla", "Sierra", "Valle", "Paz", "Lagos",
        "Méndez", "Duarte", "Osorio", "Escobar",
    ]

    def handle(self, *args, **options):
        total = sum(
            cantidad
            for hospital in self.HOSPITALES
            for _, cantidad in hospital["especialidades"]
        )

        dni_inicial = 202110010691
        colegiacion_inicial = 139

        with transaction.atomic():
            # Validar que los DNI nuevos no existan.
            dnis = [
                str(dni_inicial + i)
                for i in range(total)
            ]

            if Usuario.objects.filter(identidad__in=dnis).exists():
                raise CommandError(
                    "Algunos DNI desde 202110010691 ya existen. "
                    "No se realizaron cambios."
                )

            # Validar que las colegiaciones estén libres.
            for numero in range(
                colegiacion_inicial,
                colegiacion_inicial + total,
            ):
                codigo = f"MED-{numero:03d}"
                if Medico.objects.filter(
                    numero_colegiacion=codigo
                ).exists():
                    raise CommandError(
                        f"La colegiación {codigo} ya existe. "
                        "No se realizaron cambios."
                    )

            # Validar hospitales y especialidades antes de crear usuarios.
            asignaciones = []

            for datos in self.HOSPITALES:
                try:
                    hospital = Hospital.objects.get(
                        nombre=datos["nombre"],
                        activo=True,
                    )
                except Hospital.DoesNotExist:
                    raise CommandError(
                        f"No se encontró el hospital activo: "
                        f"{datos['nombre']}"
                    )

                for nombre, cantidad in datos["especialidades"]:
                    try:
                        especialidad = Especialidad.objects.get(
                            nombre=nombre,
                            activo=True,
                            hospitales=hospital,
                        )
                    except Especialidad.DoesNotExist:
                        raise CommandError(
                            f"'{nombre}' no está activa o no está "
                            f"asociada a {hospital.nombre}."
                        )

                    asignaciones.append(
                        (hospital, especialidad, cantidad)
                    )

            # Crear las 56 cuentas de usuario.
            usuarios = []

            for i in range(total):
                dni = dnis[i]
                nombre = self.NOMBRES[i]
                apellido = self.APELLIDOS[i]

                usuario = Usuario.objects.create_user(
                    identidad=dni,
                    password="Medico123!",
                    nombre=nombre,
                    apellido=apellido,
                    email=f"medico{dni}@example.com",
                    telefono=f"9{dni[-7:]}",
                    fecha_nacimiento=date(1990, 1, 15),
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    is_staff=False,
                )

                usuarios.append(usuario)

            # Asignar los perfiles médicos.
            indice_usuario = 0
            numero_colegiacion = colegiacion_inicial

            for hospital, especialidad, cantidad in asignaciones:
                for _ in range(cantidad):
                    usuario = usuarios[indice_usuario]

                    Medico.objects.create(
                        usuario=usuario,
                        hospital=hospital,
                        especialidad=especialidad,
                        numero_colegiacion=(
                            f"MED-{numero_colegiacion:03d}"
                        ),
                        activo=True,
                    )

                    self.stdout.write(
                        f"{usuario.identidad} | "
                        f"{hospital.nombre} | "
                        f"{especialidad.nombre} | "
                        f"MED-{numero_colegiacion:03d}"
                    )

                    indice_usuario += 1
                    numero_colegiacion += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso terminado: {total} usuarios creados "
                f"y {total} médicos asignados. "
                f"Colegiaciones MED-139 a MED-194."
            )
        )
        self.stdout.write(
            "Contraseña inicial de todos: Medico123!"
        )
