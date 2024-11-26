from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Credentials, Token
from snippets.lab4.example2_rpc_server import ServerStub
from datetime import datetime, timedelta
import unittest
import time

SERVER_PORT = 8080
TESTUSER = User(
    username='simpleuser',
    emails={'testuser@gmail.com'},
    full_name='Test User',
    role=Role.ADMIN,
    password='my_password'
)

class TestAuthentication(unittest.TestCase):
    
    def setUp(self):
        # creazione di server di test, database e servizio di autenticazione
        self.testServer = ServerStub(SERVER_PORT)
        time.sleep(3)
        self.testDatabase = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)
        self.testAuthenticationService = RemoteAuthenticationService(('localhost', SERVER_PORT))
        time.sleep(3)
        # aggiungo prima un utente
        self.testDatabase.add_user(TESTUSER)
        self.returnedToken = self.testAuthenticationService.authenticate(Credentials(TESTUSER.username, TESTUSER.password))
        return super().setUp()
    
    # test per verificare token valido
    def test_validToken(self):
        testSignature =  _compute_sha256_hash(f"{user}{expiration}{self.__secret}")
        self.assertTrue(self.testAuthenticationService.validate_token(token))
    
    # test per verificare token NON valido
    def test_authentication_failure(self):
        with self.assertRaises(RuntimeError):
            self.testAuthenticationService.authenticate(testFailCredentials)

    def tearDown(self):
        # devo chiudere il server
        self.testServer.close()
        return super().tearDown()