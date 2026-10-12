import jwt
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.crypto import constant_time_compare
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .models import Usuario
from .utils import generate_jwt_token, generate_refresh_token, decode_jwt_token


def _es_hash(valor):
    # Las claves nuevas se guardan con PBKDF2 (formato "pbkdf2_sha256$...")
    return bool(valor) and valor.startswith('pbkdf2_')


# Nota: register, login y refresh son públicos. Con authentication_classes([])
# no se intenta validar el header Authorization, así un token viejo o vencido
# que mande la app no bloquea el registro, el login ni la renovación.

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
        return Response(
            {'error': 'No se pudo registrar el usuario'},
            status=status.HTTP_400_BAD_REQUEST
        )

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
        return Response(
            {'error': 'Credenciales incorrectas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

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
    junto con un refresh token nuevo.
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

    usuario = Usuario.objects.filter(id_usuario=payload.get('id_usuario')).first()
    if not usuario:
        return Response(
            {'error': 'El usuario ya no existe'},
            status=status.HTTP_401_UNAUTHORIZED
        )


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

    return Response(_datos_perfil(usuario))

    return Response({
        'token': generate_jwt_token(usuario),
        'refresh': generate_refresh_token(usuario)
    })