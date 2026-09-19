from django.conf import settings
from django.db import models


class Notificacion(models.Model):

    class Canal(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    class Tipo(models.TextChoices):
        CONFIRMACION = "CONFIRMACION", "Confirmación"
        RECORDATORIO = "RECORDATORIO", "Recordatorio"
        CANCELACION = "CANCELACION", "Cancelación"
        REPROGRAMACION = "REPROGRAMACION", "Reprogramación"
        OFERTA = "OFERTA", "Oferta de horario"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="notificaciones"
    )

    tipo = models.CharField(max_length=20, choices=Tipo.choices)

    canal = models.CharField(max_length=10, choices=Canal.choices)

    mensaje = models.TextField()

    enviada = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    fecha_envio = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.usuario} - {self.tipo} - {self.canal}"