from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .models import Usuario
from .utils import generate_jwt_token
from .authentication import JWTAuthentication


@api_view(['POST'])
def register(request):

    nombre = request.data.get('nombre')
    dni = request.data.get('dni')
    email = request.data.get('email')
    password = request.data.get('password')

    if Usuario.objects.filter(email=email).exists():
        return Response(
            {'error': 'El email ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        Usuario.objects.create(
            nombre=nombre,
            dni=dni,
            email=email,
            password=password,
            rol=1
        )
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {'mensaje': 'Usuario registrado correctamente'},
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
def login(request):

    email = request.data.get('email')
    password = request.data.get('password')

    try:
        usuario = Usuario.objects.get(
            email=email,
            password=password
        )

        token = generate_jwt_token(usuario)

        return Response({
            'token': token,
            'id': usuario.id_usuario,
            'nombre': usuario.nombre,
            'email': usuario.email,
            'rol': usuario.rol
        })

    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Credenciales incorrectas'},
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
