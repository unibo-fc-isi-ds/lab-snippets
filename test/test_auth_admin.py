import unittest

from snippets.lab2 import address
from snippets.lab4.example2_rpc_server import ServerStub
from snippets.lab4.example3_rpc_client import LOGOUT_FAIL, LOGOUT_SUCCESS, RemoteUserAuthDatabase
from snippets.lab4.users import Credentials, Role, User

SERVER_PORT=8081
admin=User("emma", ["emma.leonardi2@studio.unibo.it", "emma@gmail.com"], "Emma Leonardi", Role.ADMIN, "password")
admin_cred=Credentials("emma", "password")
admin_cred_wrong=Credentials("emma", "wrong password")
dummyUser=User("dummy", ["dummy@gmail.com"], "Dummy McDummy", Role.USER, "dummypassword")
dummy_cred=Credentials("dummy@gmail.com", "dummypassword")

class TestAuthAdmin(unittest.TestCase):
    def setUp(self):
        #create client and server
        self.server=ServerStub(SERVER_PORT)
        self.user_db=RemoteUserAuthDatabase(address("127.0.0.1",port=SERVER_PORT)) #localhost address

    def test_add(self):
        self.user_db.add_user(user=admin)
        self.assertRaises(RuntimeError, self.user_db.add_user, admin) #user already added
        self.user_db.add_user(user=dummyUser)
    
    def test_auth(self):
        self.user_db.add_user(user=admin)
        self.user_db.add_user(dummyUser)
        self.assertRaises(RuntimeError, self.user_db.authenticate, admin_cred_wrong) #can't authenticate, credentials are wrong
        self.user_db.authenticate(credentials=admin_cred) #correct authentication
        self.user_db.get_user(id=dummy_cred.id) #this operation works because the user is logged in and is an Admin
        self.user_db.logout() #admin logs out
        self.assertRaises(RuntimeError, self.user_db.get_user, dummy_cred.id) #this operation can't be done by an unauthenticated user
        self.user_db.authenticate(credentials=dummy_cred) #dummy logs in
        self.assertRaises(RuntimeError, self.user_db.get_user, dummy_cred.id) #this operation can't be done by a regular user
        
    def test_get(self):
        self.user_db.add_user(user=admin)
        self.user_db.authenticate(credentials=admin_cred)
        self.assertRaises(RuntimeError, self.user_db.get_user, dummy_cred.id) #user not yet added to db
        self.user_db.add_user(user=dummyUser)
        dummy_got=self.user_db.get_user(dummy_cred.id) 
        tmp=dummyUser.password
        dummyUser.password=None
        self.assertEqual(dummy_got, dummyUser) #the returned user doesn't show the user password, but all of the other fields are the same
        dummyUser.password=tmp #restore the password

    def test_check(self):
        self.user_db.add_user(user=admin)
        self.user_db.authenticate(credentials=admin_cred)
        self.assertEqual(self.user_db.check_password(admin_cred),True)
        self.assertEqual(self.user_db.check_password(admin_cred_wrong),False)

    
    def test_logout(self):
        self.user_db.add_user(user=admin)
        self.assertEqual(self.user_db.logout(), LOGOUT_FAIL) #logging out without being logged in generates a fail message
        self.user_db.authenticate(credentials=admin_cred)
        self.assertEqual(self.user_db.logout(), LOGOUT_SUCCESS) #logging out after logging in generates a success message

    def tearDown(self):
        self.user_db.logout()
        self.server.close()

