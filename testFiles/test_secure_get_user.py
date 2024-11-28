from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Credentials, Token
from snippets.lab4.example2_rpc_server import ServerStub
import unittest
import time

SERVER_PORT = 8080
TESTADMIN = User(
    username='simpleadmin',
    emails={'testadmin@gmail.com'},
    full_name='Test Admin',
    role=Role.ADMIN,
    password='my_password'
)

TESTUSER = User(
    username='simpleuser',
    emails={'testuser@gmail.com'},
    full_name='Test User',
    role=Role.USER,
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
        # aggiungo prima utente e adming
        self.testDatabase.add_user(TESTADMIN)
        self.testDatabase.add_user(TESTUSER)
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(self) -> None:
        print("Closing Server")
        self.testServer.close()
        return super().tearDownClass()
    
    # test per verificare che l'admin sia riuscito a recuperare il Test User
    def test_get_user_successful(self):
        # faccio autenticare l'admin aggiungendo il token al database
        self.testDatabase.token = self.testAuthenticationService.authenticate(Credentials(TESTADMIN.username, TESTADMIN.password))
        retrievedUser = self.testDatabase.get_user(TESTUSER.username)
        retrievedUser.password = TESTUSER.password
        self.assertEquals(retrievedUser, TESTUSER)
    
    # test per verificare che venga restituito un messaggio di errore se si passa un utente normale e non un admin
    def test_get_user_failure(self):
        # faccio autenticare l'admin aggiungendo il token al database
        self.testDatabase.token = self.testAuthenticationService.authenticate(Credentials(TESTUSER.username, TESTUSER.password))
        with self.assertRaises(RuntimeError):
            self.testDatabase.get_user(TESTADMIN.username)
    
    # test per verificare che venga restituito un messaggio di errore se non viene compiuta l'autenticazione
    def test_get_user_noToken(self):
        with self.assertRaises(RuntimeError):
            self.testDatabase.get_user(TESTUSER.username)