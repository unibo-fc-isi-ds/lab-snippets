from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Token
from snippets.lab4.users.cryptography import DefaultSigner
from snippets.lab4.example2_rpc_server import ServerStub, TEST_SECRET
from datetime import datetime, timedelta
import unittest
import time

SERVER_PORT = 9091
USER = User(
    username='user123',
    emails={'test@gmail.com'},
    full_name='User',
    role=Role.ADMIN,
    password='tell_nobody'
)

class TestAuthIsSuccessful(unittest.TestCase):
    
    def setUp(self):
        self.signer = DefaultSigner(TEST_SECRET)
        self.server = ServerStub(SERVER_PORT, debug=True)
        time.sleep(3)
        self.database = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)
        self.auth_service = RemoteAuthenticationService(('localhost', SERVER_PORT))
        time.sleep(3)

        self.database.add_user(USER)
        return super().setUp()
    
    def test_token_is_valid(self):
        expiration = datetime.now() + timedelta(days=1)
        signature = self.signer.sign(USER, expiration)
        token = Token(USER, expiration, signature)
        self.assertTrue(self.auth_service.validate_token(token))

    def tearDown(self):
        time.sleep(3)
        self.server.close()
        time.sleep(3)
        return super().tearDown()