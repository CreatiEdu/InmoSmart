from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PropiedadViewSet, propiedad_detalle_mobile

router = DefaultRouter()
router.register(r'propiedades', PropiedadViewSet)

urlpatterns = [
    path("mobile/propiedades/<int:id_propiedad>/", propiedad_detalle_mobile),
] + router.urls