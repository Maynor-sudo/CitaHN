
from apps.notificaciones.models import Notificacion


def contador_notificaciones(request):
    if not request.user.is_authenticated:
        return {"notificaciones_no_leidas": 0}

    cantidad = Notificacion.objects.filter(
        usuario=request.user,
        leida=False,
    ).count()

    return {"notificaciones_no_leidas": cantidad}
