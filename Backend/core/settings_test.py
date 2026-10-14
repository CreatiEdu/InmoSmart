from .settings import *

# Solo para correr pruebas: base temporal en memoria, no toca MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Sin registro de auditoría en archivo ni caché de archivos durante los tests
LOGGING_CONFIG = None
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}