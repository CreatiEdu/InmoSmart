import datetime

import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory, APITestCase

from .authentication import JWTAuthentication
from .models import Usuario

# Prefijo donde está montado usuarios.urls en core/urls.py.
# Si tu login responde en otra ruta (por ejemplo /login/), cambialo acá.
BASE = '/api/'

CLAVE = 'Clave-Segura-2026!'


class FlujoAutenticacionTests(APITestCase):
    """
    Pruebas del registro, login, refresh token y validación del JWT.
    Usan una base de datos temporal: no tocan tus datos reales.
    """

    def setUp(self):
        self.datos = {
            'nombre': 'Prueba',
            'dni': '12345678',
            'email': 'prueba@test.com',
            'password': CLAVE,
        }

    # --- ayudas ---

    def _registrar(self):
        return self.client.post(BASE + 'register/', self.datos, format='json')

    def _login(self):
        return self.client.post(
            BASE + 'login/',
            {'email': self.datos['email'], 'password': CLAVE},
            format='json',
        )

    def _autenticar(self, token):
        request = APIRequestFactory().get('/', HTTP_AUTHORIZATION='Bearer ' + token)
        return JWTAuthentication().authenticate(request)

    def _token_vencido(self):
        payload = {
            'type': 'access',
            'id_usuario': 1,
            'exp': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    # --- registro ---

    def test_registro_guarda_la_clave_con_hash(self):
        self.assertEqual(self._registrar().status_code, 201)
        usuario = Usuario.objects.get(email=self.datos['email'])
        self.assertNotEqual(usuario.password, CLAVE)
        self.assertTrue(usuario.password.startswith('pbkdf2_'))

    def test_registro_rechaza_clave_debil(self):
        # Falla si falta AUTH_PASSWORD_VALIDATORS en settings.py
        self.datos['password'] = '123'
        self.assertEqual(self._registrar().status_code, 400)

    def test_registro_rechaza_dni_repetido(self):
        self.assertEqual(self._registrar().status_code, 201)
        self.datos['email'] = 'otro@test.com'
        self.assertEqual(self._registrar().status_code, 400)

    # --- login ---

    def test_login_devuelve_token_y_refresh(self):
        self._registrar()
        r = self._login()
        self.assertEqual(r.status_code, 200)
        self.assertIn('token', r.data)
        self.assertIn('refresh', r.data)

    def test_login_con_clave_incorrecta_da_401(self):
        self._registrar()
        r = self.client.post(
            BASE + 'login/',
            {'email': self.datos['email'], 'password': 'otra-clave'},
            format='json',
        )
        self.assertEqual(r.status_code, 401)

    def test_login_ignora_un_token_vencido_en_el_header(self):
        self._registrar()
        r = self.client.post(
            BASE + 'login/',
            {'email': self.datos['email'], 'password': CLAVE},
            format='json',
            HTTP_AUTHORIZATION='Bearer ' + self._token_vencido(),
        )
        self.assertEqual(r.status_code, 200)

    def test_usuario_viejo_con_clave_en_texto_plano_se_convierte_a_hash(self):
        Usuario.objects.create(
            nombre='Viejo', dni='87654321', email='viejo@test.com',
            password='clave-plana', rol=1,
        )
        r = self.client.post(
            BASE + 'login/',
            {'email': 'viejo@test.com', 'password': 'clave-plana'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Usuario.objects.get(email='viejo@test.com').password.startswith('pbkdf2_'))

    # --- refresh ---

    def test_refresh_devuelve_un_par_nuevo(self):
        self._registrar()
        login = self._login()
        r = self.client.post(BASE + 'refresh/', {'refresh': login.data['refresh']}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('token', r.data)
        self.assertIn('refresh', r.data)

    def test_refresh_rechaza_un_token_de_acceso(self):
        self._registrar()
        login = self._login()
        r = self.client.post(BASE + 'refresh/', {'refresh': login.data['token']}, format='json')
        self.assertEqual(r.status_code, 401)

    # --- validación del token en cada pedido ---

    def test_token_de_acceso_valido_identifica_al_usuario(self):
        self._registrar()
        login = self._login()
        usuario, _ = self._autenticar(login.data['token'])
        self.assertEqual(usuario.email, self.datos['email'])

    def test_token_de_refresco_no_sirve_como_token_de_acceso(self):
        self._registrar()
        login = self._login()
        with self.assertRaises(AuthenticationFailed):
            self._autenticar(login.data['refresh'])

    def test_token_vencido_es_rechazado(self):
        with self.assertRaises(AuthenticationFailed):
            self._autenticar(self._token_vencido())


class PoliticaClavesTests(APITestCase):
    """
    Política de claves robustas: más de 8 caracteres, letras, números
    y al menos un carácter especial. Se prueba por la API de registro.
    """

    def _registrar(self, password, n=1):
        datos = {
            'nombre': 'Prueba',
            'dni': '1000000%d' % n,
            'email': 'clave%d@test.com' % n,
            'password': password,
        }
        return self.client.post(BASE + 'register/', datos, format='json')

    def test_clave_con_solo_8_caracteres_es_rechazada(self):
        # "Más de 8": 'Abcd123!' tiene letras, número y especial, pero solo 8
        r = self._registrar('Abcd123!')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_clave_sin_caracter_especial_es_rechazada(self):
        r = self._registrar('Abcdefgh1')
        self.assertEqual(r.status_code, 400)
        self.assertIn('carácter especial', r.data['error'])

    def test_clave_sin_numero_es_rechazada(self):
        r = self._registrar('Abcdefgh!!')
        self.assertEqual(r.status_code, 400)
        self.assertIn('número', r.data['error'])

    def test_clave_sin_letra_es_rechazada(self):
        r = self._registrar('123456789!')
        self.assertEqual(r.status_code, 400)
        self.assertIn('letra', r.data['error'])

    def test_se_informan_todos_los_requisitos_que_faltan(self):
        r = self._registrar('123')
        self.assertEqual(r.status_code, 400)
        self.assertIn('letra', r.data['error'])
        self.assertIn('carácter especial', r.data['error'])

    def test_clave_de_9_caracteres_que_cumple_todo_es_aceptada(self):
        r = self._registrar('Zorro-7x!')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Usuario.objects.count(), 1)