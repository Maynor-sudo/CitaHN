
from django.core.management.base import BaseCommand
from apps.medicos.models import Medico


class Command(BaseCommand):
    help = "Lista todos los médicos, especialidades y horarios registrados."

    def handle(self, *args, **options):
        medicos = (
            Medico.objects
            .select_related(
                "usuario",
                "hospital",
                "especialidad",
            )
            .prefetch_related("disponibilidades")
            .order_by(
                "hospital__nombre",
                "especialidad__nombre",
                "usuario__apellido",
                "usuario__nombre",
            )
        )

        total = medicos.count()
        con_horario = 0
        sin_horario = 0

        self.stdout.write("=" * 110)
        self.stdout.write("REPORTE DE MÉDICOS Y HORARIOS - CITAHN")
        self.stdout.write("=" * 110)

        for medico in medicos:
            horarios = sorted(
                medico.disponibilidades.all(),
                key=lambda h: (h.dia_semana, h.hora_inicio),
            )

            self.stdout.write("\n" + "-" * 110)
            self.stdout.write(
                f"Médico: {medico.usuario.nombre} "
                f"{medico.usuario.apellido} | "
                f"DNI: {medico.usuario.identidad}"
            )
            self.stdout.write(
                f"Hospital: {medico.hospital.nombre}"
            )
            self.stdout.write(
                f"Especialidad: {medico.especialidad.nombre} | "
                f"Colegiación: {medico.numero_colegiacion} | "
                f"Activo: {'Sí' if medico.activo else 'No'}"
            )

            if not horarios:
                self.stdout.write("HORARIOS: SIN HORARIO REGISTRADO")
                sin_horario += 1
                continue

            con_horario += 1
            self.stdout.write("Horarios registrados:")

            for horario in horarios:
                estado = "Activo" if horario.activo else "Inactivo"
                self.stdout.write(
                    f"  - {horario.get_dia_semana_display()}: "
                    f"{horario.hora_inicio.strftime('%H:%M')} - "
                    f"{horario.hora_fin.strftime('%H:%M')} "
                    f"[{estado}]"
                )

        self.stdout.write("\n" + "=" * 110)
        self.stdout.write(f"Total de médicos: {total}")
        self.stdout.write(f"Médicos con horarios: {con_horario}")
        self.stdout.write(f"Médicos sin horarios: {sin_horario}")
        self.stdout.write("=" * 110)
