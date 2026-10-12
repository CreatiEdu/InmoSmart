import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .models import Usuario

class JWTAuthentication(BaseAuthentication):
    """
    Custom DRF Authentication class that validates JWT tokens.
    Expects header: Authorization: Bearer <token>
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None # Allow fallback to other auth methods or anonymous
        
        token = parts[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('El token ha expirado')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token inválido o malformado')

        # Solo se aceptan tokens de acceso (los de refresco no sirven acá).
        # Los tokens viejos, sin 'type', se siguen aceptando hasta que venzan.
        if payload.get('type', 'access') != 'access':
            raise AuthenticationFailed('Tipo de token inválido')
            
        try:
            usuario = Usuario.objects.get(id_usuario=payload.get('id_usuario'))
        except Usuario.DoesNotExist:
            raise AuthenticationFailed('El usuario asociado al token ya no existe')
            
        return (usuario, token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'