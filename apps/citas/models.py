from django.conf import settings
from django.db import models
from apps.medicos.models import Medico
from apps.hospitales.models import Hospital, Especialidad


class Cita(models.Model):
    
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        ATENDIDA = "ATENDIDA", "Atendida"
        CANCELADA = "CANCELADA", "Cancelada"
        NO_ASISTIO = "NO_ASISTIO", "No asistió"

    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="citas"
    )

    medico = models.ForeignKey(
        Medico,
        on_delete=models.PROTECT,
        related_name="citas"
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name="citas"
    )

    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.PROTECT,
        related_name="citas"
    )

    fecha_hora = models.DateTimeField()

    motivo = models.CharField(max_length=500)

    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.paciente} - "
            f"{self.fecha_hora:%d/%m/%Y %H:%M}"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["medico", "fecha_hora"],
                name="cita_medico_fecha_unica"
            )
        ]

class OfertaCita(models.Model):
    cita_origen = models.ForeignKey(
        Cita,
        on_delete=models.CASCADE,
        related_name="ofertas"
    )

    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ofertas_cita"
    )

    aceptada = models.BooleanField(
        null=True,
        blank=True
    )

    fecha_oferta = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.cita_origen} → {self.paciente}"