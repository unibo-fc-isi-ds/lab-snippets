from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Token
from snippets.lab4.example2_rpc_server import ServerStub, TEST_SECRET
from snippets.lab4.users.cryptography import DefaultSigner
from datetime import datetime, timedelta
import unittest
import time

SERVER_PORT = 8083
USER = User(
    username='user123',
    emails={'test@gmail.com'},
    full_name='User',
    role=Role.ADMIN,
    password='tell_nobody'
)

class TestAuthIsSuccessful(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.signer = DefaultSigner(TEST_SECRET)
        cls.server = ServerStub(SERVER_PORT, debug=True)
        time.sleep(3)
        cls.database = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)
        cls.auth_service = RemoteAuthenticationService(('localhost', SERVER_PORT))
        time.sleep(3)

        cls.database.add_user(USER)
    
    def test_token_is_expired(self):
        expiration = datetime.now() - timedelta(days=1)
        signature = self.signer.sign(USER, expiration)
        token = Token(USER, expiration, signature)
        self.assertFalse(self.auth_service.validate_token(token))

    def test_token_with_invalid_signature(self):
        expiration = datetime.now() + timedelta(days=1)
        signature = 'invalid signature'
        token = Token(USER, expiration, signature)
        self.assertFalse(self.auth_service.validate_token(token))

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        time.sleep(3)