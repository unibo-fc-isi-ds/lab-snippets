from threading import Thread
from time import sleep, time
import unittest
from unittest.mock import MagicMock, patch
from snippets.lab4.example2_rpc_server import ServerStub
from snippets.lab4.example3_rpc_client import RemoteUserDatabase
from snippets.lab4.users import Credentials, Role, User

class TestMultiTCPChatPeer(unittest.TestCase):
    TIMEOUT = 5
    PORT = 12345
    ADMIN_CREDS = Credentials('admin', 'admin')

    def setUp(self):
        self.server_stub = ServerStub(self.PORT)
        self.client = RemoteUserDatabase(('127.0.0.1',self.PORT))
        
    def tearDown(self):
        self.server_stub.close()
        
    def test_default_admin_login(self):
        credentials = self.ADMIN_CREDS
        token = self.client.authenticate(credentials)
        self.assertIsNotNone(token, "Token is None")
        
    def test_default_admin_login_wrong_password(self):
        credentials = Credentials('admin', 'wrong')
        try:
            self.client.authenticate(credentials)
        except RuntimeError as e:
            self.assertTrue('Invalid credentials' in str(e), "Unexpected error message")
        except Exception as e:
            self.fail("Unexpected exception: %s" % e)
        
    def test_login_wrong_username(self):
        credentials = Credentials('wrong', 'admin')
        try:
            self.client.authenticate(credentials)
        except RuntimeError as e:
            self.assertTrue('Invalid credentials' in str(e), "Unexpected error message")
        except Exception as e:
            self.fail("Unexpected exception: %s" % e)
            
    def test_get_withouth_login(self):
        self.assertRaises(RuntimeError, self.client.get_user, 'admin')
        
    def test_add_withouth_login(self):
        self.assertRaises(RuntimeError, self.client.add_user, 'admin')
        
    def test_check_withouth_login(self):
        self.assertRaises(RuntimeError, self.client.check_password, 'admin')
        
    def test_login_and_get(self):
        credentials = self.ADMIN_CREDS
        token = self.client.authenticate(credentials)
        self.assertIsNotNone(token, "Token is None")
        user = self.client.get_user('admin', token)
        self.assertEqual(user.username, 'admin', "Got wrong user")
        
    def test_login_and_add(self):
        credentials = self.ADMIN_CREDS
        token = self.client.authenticate(credentials)
        self.assertIsNotNone(token, "Token is None")
        user = User('test', ['test@localhost'], 'Test User', Role.USER, 'test')
        self.client.add_user(user, token)
        got_user = self.client.get_user('test', token)
        user.password=None
        self.assertEqual(got_user, user, "User returned is not the same as the one added")
        
    def test_unauthorized_get(self):
        credentials = self.ADMIN_CREDS
        token = self.client.authenticate(credentials)
        self.assertIsNotNone(token, "Token is None")
        user = User('test', ['test@localhost'], 'Test User', Role.USER, 'test')
        self.client.add_user(user, token)
        got_user = self.client.get_user('test', token)
        user.password=None
        self.assertEqual(got_user, user, "User returned is not the same as the one added")
        token = self.client.authenticate(Credentials('test', 'test'))
        self.assertIsNotNone(token, "Token is None")
        self.assertRaises(RuntimeError, self.client.get_user, 'admin', token)
        
        
    