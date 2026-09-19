from django.db import models


class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Hospital(models.Model):
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="hospitales"
    )

    nombre = models.CharField(max_length=150)

    direccion = models.CharField(max_length=255)

    telefono = models.CharField(max_length=20, blank=True)

    imagen = models.ImageField(
        upload_to="hospitales/",
        blank=True,
        null=True
    )

    especialidades = models.ManyToManyField(
        Especialidad,
        related_name="hospitales",
        blank=True
    )

    activo = models.BooleanField(default=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre