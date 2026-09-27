import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Usuario


class RegistroUsuarioForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ingresa una contraseña",
            }
        )
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repite tu contraseña",
            }
        )
    )

    class Meta:
        model = Usuario

        fields = (
            "identidad",
            "nombre",
            "apellido",
            "email",
            "telefono",
            "fecha_nacimiento",
        )

        widgets = {
            "identidad": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0801XXXXXXXXX",
                    "maxlength": "13",
                }
            ),

            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tu nombre",
                }
            ),

            "apellido": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tu apellido",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@ejemplo.com",
                }
            ),

            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "99999999",
                    "maxlength": "8",
                }
            ),

            "fecha_nacimiento": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def clean_identidad(self):
        identidad = self.cleaned_data["identidad"].strip()

        if not identidad.isdigit():
            raise forms.ValidationError(
                "El número de identidad debe contener solamente números."
            )

        if len(identidad) != 13:
            raise forms.ValidationError(
                "El número de identidad debe tener 13 dígitos."
            )

        if Usuario.objects.filter(identidad=identidad).exists():
            raise forms.ValidationError(
                "Este número de identidad ya está registrado."
            )

        return identidad

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Este correo electrónico ya está registrado."
            )

        return email

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()

        if not re.fullmatch(r"\d{8}", telefono):
            raise forms.ValidationError(
                "El teléfono debe contener 8 dígitos."
            )

        return telefono

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data["fecha_nacimiento"]

        if fecha > timezone.localdate():
            raise forms.ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )

        return fecha

    def clean_password1(self):
        password = self.cleaned_data["password1"]

        validate_password(password)

        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password1 != password2:
            raise forms.ValidationError(
                "Las contraseñas no coinciden."
            )

        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)

        usuario.rol = Usuario.Rol.PACIENTE
        usuario.activo = True

        usuario.set_password(
            self.cleaned_data["password1"]
        )

        if commit:
            usuario.save()

        return usuario