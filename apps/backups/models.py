from django.conf import settings
from django.db import models


class Backup(models.Model):
    nombre_archivo = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tamano = models.PositiveBigIntegerField(default=0)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Copia de seguridad"
        verbose_name_plural = "Copias de seguridad"

    def __str__(self):
        return self.nombre_archivo