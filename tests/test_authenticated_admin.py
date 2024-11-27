from snippets.lab4.example3_rpc_client import RemoteUserDatabase
from snippets.lab4.users import User, Role, Token, Credentials
from snippets.lab4.users.cryptography import DefaultSigner
from snippets.lab4.example2_rpc_server import ServerStub, TEST_SECRET
from datetime import datetime, timedelta
import unittest
import time

SERVER_PORT = 9092

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

class TestAuthenticatedAdmin(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.server = ServerStub(SERVER_PORT, debug=True)
        time.sleep(3)
        cls.database = RemoteUserDatabase(('localhost', SERVER_PORT))
        time.sleep(3)

        cls.database.add_user(ADMIN)
        cls.database.add_user(USER)

        token = cls.__create_valid_token_for_admin()
        cls.database.set_token(token)
    
    def test_authenticated_admin_gets_existing_user(self):
        response = self.database.get_user(USER.username)
        # two users are the same if they have exactly the same ids (username and email addresses)
        self.assertEqual(USER, response)

    def test_authenticated_admin_gets_non_existing_user(self):
        fake_user = User(
            username='mario',
            emails={'mario@gmail.com'},
            full_name='Mario Rossi',
            role=Role.USER,
            password='password'
        )
        with self.assertRaises(RuntimeError):
            self.database.get_user(fake_user.username)

    def test_authenticated_admin_check_password(self):
        credentials = Credentials(ADMIN.username, ADMIN.password)
        self.assertTrue(self.database.check_password(credentials))

    @classmethod
    def tearDownClass(cls):
        cls.server.close()
        time.sleep(3)
        
    @classmethod
    def __create_valid_token_for_admin(cls) -> Token:
        signer = DefaultSigner(TEST_SECRET)
        expiration = datetime.now() + timedelta(days=1)
        signature = signer.sign(ADMIN, expiration)
        return Token(ADMIN, expiration, signature)