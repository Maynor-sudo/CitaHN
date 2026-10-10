from django.contrib import admin
from django.urls import path
from apps.usuarios.views import inicio
from apps.hospitales.views import (
    seleccionar_departamento,
    seleccionar_hospital,
    seleccionar_especialidad,
)
from apps.citas.views import (
    seleccionar_horario,
    confirmar_cita,
    crear_cita_view,
    mis_citas,
    cancelar_cita_view,
)
from apps.usuarios.views import (
    inicio,
    UsuarioLoginView,
    registro,
)
from django.contrib.auth.views import LogoutView
from apps.citas.views import (
    agenda_medico,
    actualizar_estado_cita,
    reporte_pdf_medico,
)
from apps.citas.views import (
    mis_notificaciones,
    aceptar_oferta_view,
    rechazar_oferta_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", inicio, name="inicio"),
    path("citas/<int:cita_id>/cancelar/", cancelar_cita_view, name="cancelar_cita"),
    path("citas/mis-citas/", mis_citas, name="mis_citas"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/registro/", registro, name="registro"),
    path(
        "citas/departamentos/",
        seleccionar_departamento,
        name="seleccionar_departamento",
    ),
    path(
        "citas/departamentos/<int:departamento_id>/hospitales/",
        seleccionar_hospital,
        name="seleccionar_hospital",
    ),
    path(
        "citas/hospitales/<int:hospital_id>/especialidades/",
        seleccionar_especialidad,
        name="seleccionar_especialidad",
    ),
    path(
        "citas/hospitales/<int:hospital_id>/especialidades/<int:especialidad_id>/horarios/",
        seleccionar_horario,
        name="seleccionar_horario",
    ),
    path(
        "citas/hospitales/<int:hospital_id>/especialidades/<int:especialidad_id>/confirmar/",
        confirmar_cita,
        name="confirmar_cita",
    ),
    path(
        "citas/hospitales/<int:hospital_id>/especialidades/<int:especialidad_id>/crear/",
        crear_cita_view,
        name="crear_cita",
    ),
    path("accounts/login/", UsuarioLoginView.as_view(), name="login"),
    path(
        "medicos/agenda/",
        agenda_medico,
        name="agenda_medico",
    ),
    path(
        "medicos/citas/<int:cita_id>/estado/",
        actualizar_estado_cita,
        name="actualizar_estado_cita",
    ),
    path(
        "medicos/agenda/pdf/",
        reporte_pdf_medico,
        name="reporte_pdf_medico",
    ),
    path(
        "notificaciones/",
        mis_notificaciones,
        name="mis_notificaciones",
    ),
    path(
        "ofertas/<int:oferta_id>/aceptar/",
        aceptar_oferta_view,
        name="aceptar_oferta",
    ),
    path(
        "ofertas/<int:oferta_id>/rechazar/",
        rechazar_oferta_view,
        name="rechazar_oferta",
    ),
]
