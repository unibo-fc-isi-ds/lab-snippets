from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Credentials, Token
from snippets.lab4.example2_rpc_server import ServerStub
import unittest
import time

SERVER_PORT = 8081
USER = User(
    username='user123',
    emails={'test@gmail.com'},
    full_name='User',
    role=Role.ADMIN,
    password='tell_nobody'
)

class TestAuthIsSuccessful(unittest.TestCase):
    
    def setUp(self):
        self.server = ServerStub(SERVER_PORT, debug=True)
        time.sleep(3)
        self.database = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)
        self.auth_service = RemoteAuthenticationService(('localhost', SERVER_PORT))
        time.sleep(3)

        self.database.add_user(USER)
        return super().setUp()
    
    def test_authentication_is_successful(self):
        credentials = Credentials('user123', 'tell_nobody')
        token = self.auth_service.authenticate(credentials)
        self.assertIsInstance(token, Token)

    def tearDown(self):
        self.server.close()
        return super().tearDown()