from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from .models import Usuario
from .utils import generate_jwt_token


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
        hashed_password = make_password(password)

        Usuario.objects.create(
            nombre=nombre,
            dni=dni,
            email=email,
            password=hashed_password,
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
        usuario = Usuario.objects.get(email=email)

        if check_password(password, usuario.password):
            token = generate_jwt_token(usuario)

            return Response({
                'token': token,
                'id': usuario.id_usuario,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol
            }, status=status.HTTP_200_OK)

        else :
            return Response(
                {'error': 'Credenciales incorrectas'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Credenciales incorrectas'},
            status=status.HTTP_401_UNAUTHORIZED
        )