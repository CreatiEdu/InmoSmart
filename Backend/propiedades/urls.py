from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    PropiedadViewSet,
    propiedades_mobile,
    propiedad_detalle_mobile,
    favoritos_mobile,
    eliminar_favorito_mobile,
    turnos_mobile,
    cancelar_turno_mobile
)

router = DefaultRouter()
router.register(r'propiedades', PropiedadViewSet)

urlpatterns = [
    path("mobile/propiedades/", propiedades_mobile),
    path("mobile/propiedades/<int:id_propiedad>/", propiedad_detalle_mobile),
    path("mobile/favoritos/", favoritos_mobile, name="favoritos_mobile"),
    path("mobile/favoritos/<int:id_propiedad>/", eliminar_favorito_mobile, name="eliminar_favorito_mobile"),
    path("mobile/turnos/", turnos_mobile, name="turnos_mobile"),
    path("mobile/turnos/<int:id_turno>/", cancelar_turno_mobile, name="cancelar_turno_mobile"),
] + router.urls