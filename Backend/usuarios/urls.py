from django.urls import path
from .views import register, login, refresh, cerrar_sesion, perfil, baja_usuario

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('refresh/', refresh),
    path('logout/', cerrar_sesion),
    path('perfil/', perfil),
    path('baja/', baja_usuario),
]