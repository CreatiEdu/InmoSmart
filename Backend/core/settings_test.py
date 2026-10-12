from .settings import *

# Solo para correr pruebas: base temporal en memoria, no toca MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}