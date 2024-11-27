from snippets.lab4.example3_rpc_client import RemoteUserDatabase
from snippets.lab4.users import User, Role, Token
from snippets.lab4.users.cryptography import DefaultSigner
from snippets.lab4.example2_rpc_server import ServerStub, TEST_SECRET
from datetime import datetime, timedelta
import unittest
import time

SERVER_PORT = 9094

ADMIN = User(
    username='luca',
    emails={'luca@gmail.com'},
    full_name="Luca Samorè",
    role=Role.ADMIN,
    password='password'
)

USER = User(
    username='lucia',
    emails={'lucia@gmail.com'},
    full_name='Lucia Castellucci',
    role=Role.USER,
    password='password'
)

class TestUnauthenticatedAdminGetUser(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.server = ServerStub(SERVER_PORT, debug=True)
        time.sleep(3)
        cls.database = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)

        cls.database.add_user(ADMIN)
        cls.database.add_user(USER)
    
    def test_admin_without_token_get_user(self):
        with self.assertRaises(RuntimeError):
            self.database.get_user(USER.username)

    def test_authenticated_admin_gets_non_existing_user(self):
        invalid_token = self.__create_invalid_token()
        self.database.set_token(invalid_token)
        with self.assertRaises(RuntimeError):
            self.database.get_user(USER.username)

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        time.sleep(3)
        
    @classmethod
    def __create_invalid_token(cls) -> Token:
        signer = DefaultSigner(TEST_SECRET)
        expiration = datetime.now() - timedelta(days=1)
        signature = signer.sign(ADMIN, expiration)
        return Token(ADMIN, expiration, signature)