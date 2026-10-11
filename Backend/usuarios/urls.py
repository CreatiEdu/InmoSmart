from django.urls import path
from .views import register, login, perfil

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('perfil/', perfil),
]