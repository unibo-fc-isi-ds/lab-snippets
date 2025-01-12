import unittest

from snippets.lab4 import *
from snippets.lab4.example2_rpc_server import ServerStub
from snippets.lab4.example3_rpc_client import ClientStub
from snippets.lab4.example4_rpc_client_cli import *
from snippets.lab4.users import *
import time

ID = '127.0.0.1'
USER = User(
    'gio',
    emails={'gio@test.com'},
    full_name='Giorgio Garofalo',
    role=Role.ADMIN,
    password='psw'
)

class Test(unittest.TestCase):
    # Problem: even after calling server.close(), the port is still in use for a while.
    # Solution: keep track of the port number and increment it for each test.
    port = 8081

    def test_user(self):
        # Checking if the framework is working
        self.assertEqual(USER.username, 'gio')

    def setUp(self):
        port = self.__class__.port
        print('Setting up on port ', port, '...')
        self.server = ServerStub(port)
        time.sleep(1)
        self.db = RemoteUserDatabase((ID, port))
        time.sleep(1)
        self.auth = RemoteAuthenticationService((ID, port))
        time.sleep(1)
        self.db.add_user(USER)
        self.__class__.port += 1
        return super().setUp()

    def tearDown(self):
        print('Tearing down...')
        self.server.close()
        return super().tearDown()
    
    def test_auth(self):
        credentials = Credentials('gio', 'psw')
        token = self.auth.authenticate(credentials)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, Token)

    def test_auth_fail(self):
        fail = Credentials('gio', 'wrong')
        with self.assertRaises(RuntimeError):
            self.auth.authenticate(fail)

    def test_authenticated_get(self):
        credentials = Credentials('gio', 'psw')
        token = self.auth.authenticate(credentials)
        self.auth.check_privileges(self.db, credentials, token)
        self.assertEqual('gio', self.db.get_user('gio').username)

    def test_authenticated_get_fail(self):
        user2 = User(
            'gio2',
            emails={'gio2@test.com'},
            full_name='Giorgio Garofalo',
            role=Role.USER,
            password='psw'
        )
        self.db.add_user(user2)
        credentials = Credentials('gio2', 'psw')
        token = self.auth.authenticate(credentials)
        with self.assertRaises(ValueError):
            self.auth.check_privileges(self.db, credentials, token)