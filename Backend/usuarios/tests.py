import datetime

import jwt
from django.conf import settings
from django.core.cache import cache
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
        cache.clear()  # sin intentos fallidos ni tokens revocados de otros tests
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


class ControlSesionesTests(APITestCase):
    """
    Control de sesiones: cierre de sesión (revocación de tokens), refresh token
    de un solo uso y bloqueo temporal tras varios intentos fallidos de login.
    """

    def setUp(self):
        cache.clear()
        self.email = 'sesion@test.com'
        self.client.post(BASE + 'register/', {
            'nombre': 'Sesion', 'dni': '20000001',
            'email': self.email, 'password': CLAVE,
        }, format='json')

    # --- ayudas ---

    def _login(self, password=CLAVE, email=None):
        return self.client.post(
            BASE + 'login/',
            {'email': email or self.email, 'password': password},
            format='json',
        )

    def _refresh(self, token):
        return self.client.post(BASE + 'refresh/', {'refresh': token}, format='json')

    def _logout(self, refresh, access=None):
        extra = {'HTTP_AUTHORIZATION': 'Bearer ' + access} if access else {}
        return self.client.post(BASE + 'logout/', {'refresh': refresh}, format='json', **extra)

    def _autenticar(self, token):
        request = APIRequestFactory().get('/', HTTP_AUTHORIZATION='Bearer ' + token)
        return JWTAuthentication().authenticate(request)

    # --- cierre de sesión ---

    def test_logout_revoca_el_refresh_token(self):
        login = self._login()
        self.assertEqual(self._logout(login.data['refresh']).status_code, 200)
        self.assertEqual(self._refresh(login.data['refresh']).status_code, 401)

    def test_logout_revoca_tambien_el_token_de_acceso(self):
        login = self._login()
        self.assertIsNotNone(self._autenticar(login.data['token']))  # antes sirve
        self._logout(login.data['refresh'], access=login.data['token'])
        with self.assertRaises(AuthenticationFailed):
            self._autenticar(login.data['token'])

    def test_logout_sin_refresh_token_da_400(self):
        r = self.client.post(BASE + 'logout/', {}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_logout_se_puede_repetir(self):
        login = self._login()
        self.assertEqual(self._logout(login.data['refresh']).status_code, 200)
        self.assertEqual(self._logout(login.data['refresh']).status_code, 200)

    def test_cerrar_una_sesion_no_cierra_las_otras(self):
        # Dos dispositivos con la misma cuenta: cerrar uno no afecta al otro
        a = self._login()
        b = self._login()
        self._logout(a.data['refresh'], access=a.data['token'])
        self.assertEqual(self._refresh(b.data['refresh']).status_code, 200)

    # --- refresh token de un solo uso ---

    def test_el_refresh_token_solo_se_puede_usar_una_vez(self):
        login = self._login()
        primero = self._refresh(login.data['refresh'])
        self.assertEqual(primero.status_code, 200)
        segundo = self._refresh(login.data['refresh'])
        self.assertEqual(segundo.status_code, 401)

    def test_el_refresh_token_nuevo_si_funciona(self):
        login = self._login()
        nuevo = self._refresh(login.data['refresh'])
        self.assertEqual(self._refresh(nuevo.data['refresh']).status_code, 200)

    # --- bloqueo por intentos fallidos ---

    def test_bloquea_despues_de_5_intentos_fallidos(self):
        for _ in range(5):
            self.assertEqual(self._login('incorrecta').status_code, 401)
        self.assertEqual(self._login('incorrecta').status_code, 429)

    def test_con_la_cuenta_bloqueada_ni_la_clave_correcta_entra(self):
        for _ in range(5):
            self._login('incorrecta')
        self.assertEqual(self._login(CLAVE).status_code, 429)

    def test_un_login_exitoso_reinicia_el_contador(self):
        for _ in range(4):
            self._login('incorrecta')
        self.assertEqual(self._login(CLAVE).status_code, 200)
        for _ in range(4):
            self.assertEqual(self._login('incorrecta').status_code, 401)

    def test_el_bloqueo_no_revela_si_el_correo_existe(self):
        # Un correo inexistente se bloquea igual que uno real
        for _ in range(5):
            self.assertEqual(self._login('x', email='noexiste@test.com').status_code, 401)
        self.assertEqual(self._login('x', email='noexiste@test.com').status_code, 429)

    def test_el_bloqueo_de_un_correo_no_afecta_a_otro(self):
        for _ in range(5):
            self._login('incorrecta')
        self.assertEqual(self._login('incorrecta').status_code, 429)
        self.client.post(BASE + 'register/', {
            'nombre': 'Otro', 'dni': '20000002',
            'email': 'otro@test.com', 'password': CLAVE,
        }, format='json')
        self.assertEqual(self._login(CLAVE, email='otro@test.com').status_code, 200)


class AuditoriaTests(APITestCase):
    """
    Auditoría: cada acción importante deja una línea en el registro 'auditoria'
    (quién, qué, desde qué IP) y nunca se guardan claves ni tokens.
    """

    def setUp(self):
        cache.clear()
        self.email = 'audit@test.com'
        self.client.post(BASE + 'register/', {
            'nombre': 'Audit', 'dni': '30000001',
            'email': self.email, 'password': CLAVE,
        }, format='json')

    def _login(self, password=CLAVE, email=None, **extra):
        return self.client.post(
            BASE + 'login/',
            {'email': email or self.email, 'password': password},
            format='json', **extra,
        )

    def _lineas(self, contexto):
        return [r.getMessage() for r in contexto.records]

    def test_el_registro_de_usuario_se_audita(self):
        with self.assertLogs('auditoria', 'INFO') as cm:
            self.client.post(BASE + 'register/', {
                'nombre': 'Nuevo', 'dni': '30000002',
                'email': 'nuevo@test.com', 'password': CLAVE,
            }, format='json')
        self.assertTrue(any('REGISTRO_OK' in l and 'nuevo@test.com' in l for l in self._lineas(cm)))

    def test_un_registro_rechazado_se_audita(self):
        with self.assertLogs('auditoria', 'INFO') as cm:
            self.client.post(BASE + 'register/', {
                'nombre': 'Otro', 'dni': '30000003',
                'email': 'otro@test.com', 'password': 'debil',
            }, format='json')
        self.assertTrue(any('REGISTRO_FALLIDO' in l for l in self._lineas(cm)))

    def test_login_exitoso_se_audita_con_el_id_del_usuario(self):
        with self.assertLogs('auditoria', 'INFO') as cm:
            self._login()
        linea = [l for l in self._lineas(cm) if 'LOGIN_OK' in l][0]
        self.assertIn('id=', linea)
        self.assertIn(self.email, linea)

    def test_login_fallido_se_audita(self):
        with self.assertLogs('auditoria', 'INFO') as cm:
            self._login(password='Incorrecta-123!')
        self.assertTrue(any('LOGIN_FALLIDO' in l and self.email in l for l in self._lineas(cm)))

    def test_el_bloqueo_de_la_cuenta_se_audita(self):
        for _ in range(5):
            self._login(password='Incorrecta-123!')
        with self.assertLogs('auditoria', 'INFO') as cm:
            self._login()
        self.assertTrue(any('LOGIN_BLOQUEADO' in l for l in self._lineas(cm)))

    def test_refresh_y_logout_se_auditan(self):
        login = self._login()
        with self.assertLogs('auditoria', 'INFO') as cm:
            nuevo = self.client.post(BASE + 'refresh/', {'refresh': login.data['refresh']}, format='json')
            self.client.post(BASE + 'logout/', {'refresh': nuevo.data['refresh']}, format='json')
        texto = '\n'.join(self._lineas(cm))
        self.assertIn('REFRESH_OK', texto)
        self.assertIn('LOGOUT', texto)

    def test_reusar_un_refresh_token_se_audita(self):
        login = self._login()
        viejo = login.data['refresh']
        self.client.post(BASE + 'refresh/', {'refresh': viejo}, format='json')
        with self.assertLogs('auditoria', 'INFO') as cm:
            self.client.post(BASE + 'refresh/', {'refresh': viejo}, format='json')
        self.assertTrue(any('REFRESH_RECHAZADO' in l for l in self._lineas(cm)))

    def test_la_actualizacion_del_perfil_se_audita(self):
        login = self._login()
        with self.assertLogs('auditoria', 'INFO') as cm:
            self.client.put(
                BASE + 'perfil/',
                {'nombre': 'Audit 2', 'email': self.email, 'dni': '30000001', 'telefono': '3511234567'},
                format='json',
                HTTP_AUTHORIZATION='Bearer ' + login.data['token'],
            )
        self.assertTrue(any('PERFIL_ACTUALIZADO' in l for l in self._lineas(cm)))

    def test_nunca_se_registran_claves_ni_tokens(self):
        with self.assertLogs('auditoria', 'INFO') as cm:
            login = self._login()
            self._login(password='Incorrecta-123!')
            self.client.post(BASE + 'logout/', {'refresh': login.data['refresh']}, format='json')
        texto = '\n'.join(self._lineas(cm))
        for secreto in (CLAVE, 'Incorrecta-123!', login.data['token'], login.data['refresh']):
            self.assertNotIn(secreto, texto)

    def test_se_registra_la_ip_de_origen(self):
        with self.assertLogs('auditoria', 'INFO') as cm:
            self._login(HTTP_X_FORWARDED_FOR='190.1.2.3, 10.0.0.1')
        self.assertTrue(any('ip=190.1.2.3' in l for l in self._lineas(cm)))

    def test_un_correo_con_saltos_de_linea_no_falsifica_el_registro(self):
        with self.assertLogs('auditoria', 'INFO') as cm:
            self._login(password='x', email='a@b.com\nLOGIN_OK | id=1')
        for linea in self._lineas(cm):
            self.assertNotIn('\n', linea)