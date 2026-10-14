import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.crypto import constant_time_compare
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Usuario
from .utils import (
    generate_jwt_token, generate_refresh_token, decode_jwt_token,
    revocar_token, esta_revocado,
)
from .authentication import JWTAuthentication
from .auditoria import registrar as auditar


def _es_hash(valor):
    # Las claves nuevas se guardan con PBKDF2 (formato "pbkdf2_sha256$...")
    return bool(valor) and valor.startswith('pbkdf2_')


# --- Control de sesiones: bloqueo por intentos fallidos de login ---
# Se cuentan por correo (exista o no la cuenta, para no revelar cuáles existen).
# Se configura en settings.py con LOGIN_MAX_INTENTOS y LOGIN_BLOQUEO_MINUTOS.

def _clave_intentos(email):
    return 'login_fallidos:' + str(email or '').strip().lower()


def _login_bloqueado(email):
    maximo = getattr(settings, 'LOGIN_MAX_INTENTOS', 5)
    return cache.get(_clave_intentos(email), 0) >= maximo


def _registrar_fallo_login(email):
    minutos = getattr(settings, 'LOGIN_BLOQUEO_MINUTOS', 15)
    clave = _clave_intentos(email)
    cache.set(clave, cache.get(clave, 0) + 1, minutos * 60)


def _limpiar_fallos_login(email):
    cache.delete(_clave_intentos(email))


# Nota: register, login, refresh y logout son públicos. Con
# authentication_classes([]) no se intenta validar el header Authorization,
# así un token viejo o vencido que mande la app no bloquea el registro,
# el login, la renovación ni el cierre de sesión.

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def register(request):

    nombre = request.data.get('nombre')
    dni = request.data.get('dni')
    email = request.data.get('email')
    password = request.data.get('password')

    if not all([nombre, dni, email, password]):
        return Response(
            {'error': 'Faltan datos obligatorios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Usuario.objects.filter(email=email).exists():
        auditar('REGISTRO_FALLIDO', request, email=email, detalle='email ya registrado')
        return Response(
            {'error': 'El email ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(str(dni)) > 9:
        return Response(
            {'error': 'El DNI no es válido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Usuario.objects.filter(dni=dni).exists():
        return Response(
            {'error': 'El DNI ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clave segura: aplica los validadores de AUTH_PASSWORD_VALIDATORS
    try:
        validate_password(password)
    except ValidationError as e:
        auditar('REGISTRO_FALLIDO', request, email=email, detalle='clave no cumple la política')
        return Response(
            {'error': ' '.join(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        Usuario.objects.create(
            nombre=nombre,
            dni=dni,
            email=email,
            password=make_password(password),  # se guarda el hash, nunca la clave
            rol=1
        )
    except Exception:
        auditar('REGISTRO_FALLIDO', request, email=email, detalle='error al guardar')
        return Response(
            {'error': 'No se pudo registrar el usuario'},
            status=status.HTTP_400_BAD_REQUEST
        )

    auditar('REGISTRO_OK', request, email=email)
    return Response(
        {'mensaje': 'Usuario registrado correctamente'},
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):

    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'error': 'Credenciales incorrectas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Demasiados intentos fallidos: se bloquea sin ni siquiera mirar la clave
    if _login_bloqueado(email):
        auditar('LOGIN_BLOQUEADO', request, email=email, detalle='demasiados intentos fallidos')
        minutos = getattr(settings, 'LOGIN_BLOQUEO_MINUTOS', 15)
        return Response(
            {'error': 'Demasiados intentos fallidos. Probá de nuevo en %d minutos.' % minutos},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    usuario = Usuario.objects.filter(email=email).first()
    credenciales_ok = False

    if usuario:
        if _es_hash(usuario.password):
            credenciales_ok = check_password(password, usuario.password)
        elif constant_time_compare(usuario.password, password):
            # Usuario viejo con clave en texto plano: entra y se convierte a hash
            credenciales_ok = True
            usuario.password = make_password(password)
            usuario.save(update_fields=['password'])

    if not credenciales_ok:
        _registrar_fallo_login(email)
        auditar('LOGIN_FALLIDO', request, email=email, detalle='credenciales incorrectas')
        return Response(
            {'error': 'Credenciales incorrectas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    _limpiar_fallos_login(email)
    auditar('LOGIN_OK', request, usuario=usuario)

    token = generate_jwt_token(usuario)
    refresh_token = generate_refresh_token(usuario)

    return Response({
        'token': token,
        'refresh': refresh_token,
        'id': usuario.id_usuario,
        'nombre': usuario.nombre,
        'email': usuario.email,
        'rol': usuario.rol
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def refresh(request):
    """
    Recibe {"refresh": "<token>"} y devuelve un token de acceso nuevo
    junto con un refresh token nuevo. El refresh token usado queda revocado
    (solo se puede usar una vez).
    """
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response(
            {'error': 'Falta el refresh token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        payload = decode_jwt_token(refresh_token)
    except jwt.ExpiredSignatureError:
        return Response(
            {'error': 'La sesión expiró, iniciá sesión de nuevo'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except jwt.InvalidTokenError:
        return Response(
            {'error': 'Token inválido'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Solo se aceptan tokens de refresco (un token de acceso no sirve acá)
    if payload.get('type') != 'refresh':
        return Response(
            {'error': 'Token inválido'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Sesión cerrada o refresh token ya usado
    if esta_revocado(payload):
        auditar('REFRESH_RECHAZADO', request, detalle='refresh token revocado o ya usado')
        return Response(
            {'error': 'La sesión fue cerrada, iniciá sesión de nuevo'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    usuario = Usuario.objects.filter(id_usuario=payload.get('id_usuario')).first()
    if not usuario:
        return Response(
            {'error': 'El usuario ya no existe'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Rotación: el refresh token usado ya no sirve más
    revocar_token(payload)
    auditar('REFRESH_OK', request, usuario=usuario)

    return Response({
        'token': generate_jwt_token(usuario),
        'refresh': generate_refresh_token(usuario)
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def cerrar_sesion(request):
    """
    Cierra la sesión: revoca el refresh token ({"refresh": "<token>"}) y, si la
    app manda el header Authorization, también el token de acceso.
    Es idempotente: cerrar una sesión ya cerrada responde igual.
    """
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response(
            {'error': 'Falta el refresh token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    quien = None
    try:
        payload = decode_jwt_token(refresh_token)
        if payload.get('type') == 'refresh':
            revocar_token(payload)
            quien = Usuario.objects.filter(id_usuario=payload.get('id_usuario')).first()
    except jwt.InvalidTokenError:
        pass  # vencido o inválido: no hay nada que revocar

    partes = request.headers.get('Authorization', '').split()
    if len(partes) == 2 and partes[0].lower() == 'bearer':
        try:
            payload = decode_jwt_token(partes[1])
            if payload.get('type') == 'access':
                revocar_token(payload)
        except jwt.InvalidTokenError:
            pass

    auditar('LOGOUT', request, usuario=quien)
    return Response({'mensaje': 'Sesión cerrada'})


def _datos_perfil(usuario):
    # Solo estos datos salen hacia la app (nunca la contraseña)
    return {
        'nombre': usuario.nombre,
        'email': usuario.email,
        'dni': usuario.dni,
        'telefono': usuario.telefono or ''
    }


@api_view(['GET', 'PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def perfil(request):
    usuario = request.user  # el usuario dueño del token

    if request.method == 'GET':
        return Response(_datos_perfil(usuario))

    # PUT: actualizar datos del perfil
    nombre = (request.data.get('nombre') or '').strip()
    email = (request.data.get('email') or '').strip()
    dni = (request.data.get('dni') or '').strip()
    telefono = (request.data.get('telefono') or '').strip()

    if not nombre or not email or not dni:
        return Response(
            {'error': 'Complete usuario, DNI y correo'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {'error': 'El correo electrónico no es válido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(dni) < 7 or len(dni) > 9 or not dni.isdigit():
        return Response(
            {'error': 'El DNI debe tener entre 7 y 9 números'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(telefono) > 50:
        return Response(
            {'error': 'El teléfono es demasiado largo'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Usuario.objects.exclude(pk=usuario.pk).filter(email=email).exists():
        return Response(
            {'error': 'Ese correo ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Usuario.objects.exclude(pk=usuario.pk).filter(dni=dni).exists():
        return Response(
            {'error': 'Ese DNI ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    usuario.nombre = nombre
    usuario.email = email
    usuario.dni = dni
    usuario.telefono = telefono if telefono else None
    usuario.save()
    auditar('PERFIL_ACTUALIZADO', request, usuario=usuario)

    return Response(_datos_perfil(usuario))