
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.usuarios.models import Usuario
from apps.hospitales.models import Hospital, Especialidad
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Asigna médicos a los hospitales 16 al 20 de CitaHN."

    HOSPITALES = [
        {
            "nombre": "Hospital Puerto Lempira",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital María de Especialidades Pediátricas",
            "especialidades": [
                ("Pediatría", 1),
                ("Cardiología Pediátrica", 1),
                ("Cirugía Cardiovascular Pediátrica", 1),
                ("Neurología Pediátrica", 1),
                ("Gastroenterología Pediátrica", 1),
                ("Endocrinología Pediátrica", 1),
                ("Nefrología Pediátrica", 1),
                ("Odontología Pediátrica", 1),
            ],
        },
        {
            "nombre": "Hospital Enrique Aguilar Cerrato",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
        {
            "nombre": "Hospital de Roatán",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Ortopedia", 1),
            ],
        },
        {
            "nombre": "Hospital Roberto Suazo Córdova",
            "especialidades": [
                ("Medicina General", 2),
                ("Medicina Interna", 1),
                ("Pediatría", 1),
                ("Ginecología y Obstetricia", 1),
                ("Cirugía General", 1),
            ],
        },
    ]

    def handle(self, *args, **options):
        asignaciones = []
        total_medicos = sum(
            cantidad
            for hospital in self.HOSPITALES
            for _, cantidad in hospital["especialidades"]
        )

        with transaction.atomic():
            numero_inicial = 107
            numero_final = numero_inicial + total_medicos - 1

            for numero in range(numero_inicial, numero_final + 1):
                colegiacion = f"MED-{numero:03d}"
                if Medico.objects.filter(
                    numero_colegiacion=colegiacion
                ).exists():
                    raise CommandError(
                        f"Ya existe la colegiación {colegiacion}. "
                        "No se realizaron asignaciones."
                    )

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

                for nombre_especialidad, cantidad in datos["especialidades"]:
                    try:
                        especialidad = Especialidad.objects.get(
                            nombre=nombre_especialidad,
                            activo=True,
                            hospitales=hospital,
                        )
                    except Especialidad.DoesNotExist:
                        raise CommandError(
                            f"La especialidad '{nombre_especialidad}' "
                            f"no está activa o no está asociada a "
                            f"{hospital.nombre}."
                        )

                    asignaciones.append(
                        (hospital, especialidad, cantidad)
                    )

            usuarios = list(
                Usuario.objects.filter(
                    rol=Usuario.Rol.MEDICO,
                    activo=True,
                    perfil_medico__isnull=True,
                ).order_by("identidad")[:total_medicos]
            )

            if len(usuarios) < total_medicos:
                raise CommandError(
                    f"Se necesitan {total_medicos} usuarios médicos "
                    f"sin perfil, pero solo hay {len(usuarios)}."
                )

            indice_usuario = 0
            numero_colegiacion = numero_inicial

            for hospital, especialidad, cantidad in asignaciones:
                for _ in range(cantidad):
                    usuario = usuarios[indice_usuario]
                    indice_usuario += 1

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
                        f"Asignado: {usuario.nombre} "
                        f"{usuario.apellido} | {hospital.nombre} | "
                        f"{especialidad.nombre} | "
                        f"MED-{numero_colegiacion:03d}"
                    )

                    numero_colegiacion += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso terminado: {total_medicos} médicos asignados. "
                f"Colegiaciones MED-107 a MED-138."
            )
        )
