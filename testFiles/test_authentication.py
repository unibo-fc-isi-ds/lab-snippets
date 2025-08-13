from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Credentials, Token
from snippets.lab4.example2_rpc_server import ServerStub
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
    
    @classmethod
    def setUpClass(self):
        # creazione di server di test, database e servizio di autenticazione
        self.testServer = ServerStub(SERVER_PORT)
        time.sleep(3)
        self.testDatabase = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)
        self.testAuthenticationService = RemoteAuthenticationService(('localhost', SERVER_PORT))
        time.sleep(3)
        # aggiungo prima un utente
        self.testDatabase.add_user(TESTUSER)
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(self) -> None:
        print("Closing Server")
        self.testServer.close()
        return super().tearDownClass()
    
    # test per verificare corretta autenticazione
    def test_authentication_successful(self):
        testCredentials = Credentials('simpleuser', 'my_password')
        returnedToken = self.testAuthenticationService.authenticate(testCredentials)
        self.assertIsInstance(returnedToken, Token)
    
    # test per verificare autenticazione errata data password sbagliata
    def test_authentication_failure(self):
        testFailCredentials = Credentials('simpleuser', 'wrong_answer')
        with self.assertRaises(RuntimeError):
            self.testAuthenticationService.authenticate(testFailCredentials)
    
    # test per verificare autenticazione errata dato user non esistente nel database
    def test_authentication_failure_missingUser(self):
        testFailCredentials = Credentials('user', 'my_password')
        with self.assertRaises(RuntimeError):
            self.testAuthenticationService.authenticate(testFailCredentials)