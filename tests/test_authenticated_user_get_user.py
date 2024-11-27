from snippets.lab4.example3_rpc_client import RemoteUserDatabase
from snippets.lab4.users import User, Role, Token
from snippets.lab4.users.cryptography import DefaultSigner
from snippets.lab4.example2_rpc_server import ServerStub, TEST_SECRET
from datetime import datetime, timedelta
import unittest
import time

SERVER_PORT = 9093

REQUESTER = User(
    username='luca',
    emails={'luca@gmail.com'},
    full_name="Luca Samore",
    role=Role.USER,
    password='password'
)

USER = User(
    username='lucia',
    emails={'lucia@gmail.com'},
    full_name='Lucia Castellucci',
    role=Role.USER,
    password='password'
)

class TestAuthenticatedUserGetUser(unittest.TestCase):
    
    def setUp(self):
        self.server = ServerStub(SERVER_PORT, debug=True)
        time.sleep(3)
        self.database = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)

        self.database.add_user(REQUESTER)
        self.database.add_user(USER)

        token = self.__create_valid_token()
        self.database.set_token(token)
    
    def test_authenticated_user_get_user(self):
        with self.assertRaises(RuntimeError):
            self.database.get_user(USER.username)

    def tearDown(self):
        self.server.close()
        time.sleep(3)
        
    def __create_valid_token(self) -> Token:
        signer = DefaultSigner(TEST_SECRET)
        expiration = datetime.now() + timedelta(days=1)
        signature = signer.sign(REQUESTER, expiration)
        return Token(REQUESTER, expiration, signature)