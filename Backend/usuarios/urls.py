from django.urls import path
from .views import register, login, refresh, perfil

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('refresh/', refresh),
    path('perfil/', perfil),
]