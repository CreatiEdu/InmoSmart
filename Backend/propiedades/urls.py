from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PropiedadViewSet, propiedades_mobile

router = DefaultRouter()
router.register(r'propiedades', PropiedadViewSet)

urlpatterns = [
    path("mobile/propiedades/", propiedades_mobile),
] + router.urls