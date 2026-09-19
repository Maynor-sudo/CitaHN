from django.conf import settings
from django.db import models
from apps.hospitales.models import Hospital, Especialidad


class Medico(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="perfil_medico"
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name="medicos"
    )

    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.PROTECT,
        related_name="medicos"
    )

    numero_colegiacion = models.CharField(
        max_length=50,
        unique=True
    )

    activo = models.BooleanField(default=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.usuario.nombre} {self.usuario.apellido}"

class Disponibilidad(models.Model):

    class DiaSemana(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    medico = models.ForeignKey(
        Medico,
        on_delete=models.CASCADE,
        related_name="disponibilidades"
    )

    dia_semana = models.IntegerField(
        choices=DiaSemana.choices
    )

    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["dia_semana", "hora_inicio"]

    def __str__(self):
        return (
            f"{self.medico} - "
            f"{self.get_dia_semana_display()} "
            f"{self.hora_inicio} - {self.hora_fin}"
        )

class BloqueoHorario(models.Model):
    medico = models.ForeignKey(
        Medico,
        on_delete=models.CASCADE,
        related_name="bloqueos"
    )

    inicio = models.DateTimeField()
    fin = models.DateTimeField()

    motivo = models.CharField(
        max_length=255,
        blank=True
    )

    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.medico} - {self.inicio} a {self.fin}"