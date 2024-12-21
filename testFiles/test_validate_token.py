from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Credentials, Token
from snippets.lab4.example2_rpc_server import ServerStub
from datetime import datetime, timedelta
import unittest
import time
import uuid
import hashlib

SERVER_PORT = 8080
TESTUSER = User(
    username='simpleuser',
    emails={'testuser@gmail.com'},
    full_name='Test User',
    role=Role.ADMIN,
    password='my_password'
)

def _compute_sha256_hash(input: str) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input.encode('utf-8'))
    return sha256_hash.hexdigest()

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
    
    # test per verificare token valido
    def test_valid_token(self):
        returnedToken = self.testAuthenticationService.authenticate(Credentials(TESTUSER.username, TESTUSER.password))
        self.assertTrue(self.testAuthenticationService.validate_token(returnedToken))
    
    # test per verificare token NON valido
    def test_incorrect_token(self):
        secret = str(uuid.uuid4())
        testExpiration = datetime.now() + timedelta(days=1)
        testSignature =  _compute_sha256_hash(f"{TESTUSER.username}{testExpiration}{secret}")
        testWrongToken = Token(TESTUSER, testExpiration, testSignature)
        self.assertFalse(self.testAuthenticationService.validate_token(testWrongToken))
    
    # test per verificare token che è ormai scaduto
    def test_expired_token(self):
        testWrongExpiration = datetime.now() - timedelta(days=1)
        returnedToken = self.testAuthenticationService.authenticate(Credentials(TESTUSER.username, TESTUSER.password))
        testExpiredToken = Token(returnedToken.user, testWrongExpiration, returnedToken.signature)
        self.assertFalse(self.testAuthenticationService.validate_token(testExpiredToken))