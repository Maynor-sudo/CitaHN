from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect

from .forms import RegistroUsuarioForm


def inicio(request):
    return render(request, "usuarios/inicio.html")


class UsuarioLoginView(LoginView):
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True


def registro(request):

    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")

    else:
        form = RegistroUsuarioForm()

    return render(
        request,
        "usuarios/registro.html",
        {"form": form}
    )