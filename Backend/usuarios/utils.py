import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings

# Duración de los tokens. Se pueden cambiar desde settings.py con
# JWT_ACCESS_MINUTES y JWT_REFRESH_DAYS (por defecto: acceso 1 día, refresco 7 días).
ACCESS_LIFETIME = timedelta(minutes=getattr(settings, 'JWT_ACCESS_MINUTES', 1440))
REFRESH_LIFETIME = timedelta(days=getattr(settings, 'JWT_REFRESH_DAYS', 7))


def generate_jwt_token(usuario):
    """
    Genera el token de acceso (el que se envía en cada pedido).
    """
    now = datetime.now(timezone.utc)
    payload = {
        'type': 'access',
        'id_usuario': usuario.id_usuario,
        'nombre': usuario.nombre,
        'email': usuario.email,
        'rol': usuario.rol,
        'exp': now + ACCESS_LIFETIME,
        'iat': now
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def generate_refresh_token(usuario):
    """
    Genera el token de refresco. Solo sirve para pedir un nuevo token de acceso,
    por eso lleva lo mínimo y el tipo 'refresh'.
    """
    now = datetime.now(timezone.utc)
    payload = {
        'type': 'refresh',
        'id_usuario': usuario.id_usuario,
        'exp': now + REFRESH_LIFETIME,
        'iat': now
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def decode_jwt_token(token):
    """
    Decodifica y valida un token JWT.
    Devuelve el payload si es válido, o lanza la excepción de jwt correspondiente.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])