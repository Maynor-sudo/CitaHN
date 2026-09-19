from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):

    def create_user(self, identidad, password=None, **extra_fields):
        if not identidad:
            raise ValueError("El DNI es obligatorio.")

        usuario = self.model(
            identidad=identidad,
            **extra_fields
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, identidad, password=None, **extra_fields):
        extra_fields.setdefault("rol", "ADMIN")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("activo", True)

        return self.create_user(identidad, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):

    class Rol(models.TextChoices):
        PACIENTE = "PACIENTE", "Paciente"
        MEDICO = "MEDICO", "Médico"
        ADMIN = "ADMIN", "Administrador"

    identidad = models.CharField(
        max_length=13,
        unique=True
    )

    nombre = models.CharField(max_length=100)

    apellido = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    telefono = models.CharField(max_length=20)

    fecha_nacimiento = models.DateField()

    rol = models.CharField(
        max_length=10,
        choices=Rol.choices,
        default=Rol.PACIENTE
    )

    activo = models.BooleanField(default=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = "identidad"

    REQUIRED_FIELDS = [
        "nombre",
        "apellido",
        "email",
        "telefono",
        "fecha_nacimiento",
    ]

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.identidad}"