from snippets.lab4.example2_rpc_server import ServerStub
from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.users import User, Role, Credentials, Token
import unittest
import time

SERVER_PORT = 8081

class TestAuthIsUnsuccessful(unittest.TestCase):
    
    def setUp(self):
        self.server = ServerStub(SERVER_PORT, debug=True)
        time.sleep(3)
        self.database = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)
        self.auth_service = RemoteAuthenticationService(('localhost', SERVER_PORT))
        time.sleep(3)
        return super().setUp()
    
    def test_authentication_is_unsuccessful(self):
        credentials = Credentials('user456', 'tell_nobody_2')
        with self.assertRaises(RuntimeError):
            self.auth_service.authenticate(credentials)

    def tearDown(self):
        time.sleep(3)
        self.server.close()
        time.sleep(3)
        return super().tearDown()