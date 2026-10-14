"""
Auditoría: deja registro de quién hizo qué y cuándo.

Cada evento es una línea en el archivo auditoria/auditoria.log (ver LOGGING en
settings.py), con este formato:

    2026-10-14 10:15:02 | LOGIN_FALLIDO | email=ana@mail.com | ip=190.1.2.3 | detalle=clave incorrecta

Nunca se guardan claves ni tokens: solo quién (correo / id), qué, desde dónde y cuándo.
"""
import logging

logger = logging.getLogger('auditoria')


def _ip(request):
    # Detrás del proxy de PythonAnywhere la IP real llega en X-Forwarded-For
    reenviada = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if reenviada:
        return reenviada.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '-')


def _limpio(valor):
    # Sin saltos de línea: evita que alguien "falsifique" líneas del registro
    return str(valor).replace('\r', ' ').replace('\n', ' ')[:200]


def registrar(evento, request, email=None, usuario=None, detalle=''):
    """Registra un evento de auditoría. Nunca rompe el pedido si algo falla."""
    try:
        partes = [evento]
        if usuario is not None:
            partes.append('id=%s' % usuario.id_usuario)
            email = email or usuario.email
        if email:
            partes.append('email=%s' % _limpio(email))
        partes.append('ip=%s' % _limpio(_ip(request)))
        if detalle:
            partes.append('detalle=%s' % _limpio(detalle))
        logger.info(' | '.join(partes))
    except Exception:
        pass