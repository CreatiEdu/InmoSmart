from django.core.exceptions import ValidationError


class ComplejidadClaveValidator:
    """
    Política de claves del proyecto: la clave debe combinar letras, números
    y al menos un carácter especial. El largo mínimo lo controla
    MinimumLengthValidator (ver AUTH_PASSWORD_VALIDATORS en settings.py).

    Se informan todos los requisitos que faltan juntos, así el usuario
    corrige la clave de una sola vez.
    """

    def validate(self, password, user=None):
        errores = []

        if not any(c.isalpha() for c in password):
            errores.append(ValidationError(
                'La contraseña debe contener al menos una letra.',
                code='clave_sin_letra',
            ))
        if not any(c.isdigit() for c in password):
            errores.append(ValidationError(
                'La contraseña debe contener al menos un número.',
                code='clave_sin_numero',
            ))
        if not any((not c.isalnum()) and (not c.isspace()) for c in password):
            errores.append(ValidationError(
                'La contraseña debe contener al menos un carácter especial '
                '(por ejemplo ! @ # $ % - _).',
                code='clave_sin_especial',
            ))

        if errores:
            raise ValidationError(errores)

    def get_help_text(self):
        return 'Debe incluir letras, números y al menos un carácter especial.'