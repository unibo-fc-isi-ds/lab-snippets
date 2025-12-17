import time
from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self._server_address = address(*server_address)

    def rpc(self, name, *args, token = None):
        client = Client(self._server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, token)
            print('# Marshalling', request, 'towards', "%s:%d" % client.remote_address)
            request = serialize(request)
            print('# Sending message:', request.replace('\n', '\n# '))
            client.send(request)
            response = client.receive()
            print('# Received message:', response.replace('\n', '\n# '))
            response = deserialize(response)
            assert isinstance(response, Response)
            print('# Unmarshalled', response, 'from', "%s:%d" % client.remote_address)
            if response.error:
                raise RuntimeError(response.error)
            return response.result
        finally:
            client.close()
            print('# Disconnected from %s:%d' % client.remote_address)


class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)
        self.token = None

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id, token=self.token)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials, token=self.token)

class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, user_db: RemoteUserDatabase):
        super().__init__(user_db._server_address)
        self.linked_user_db = user_db

    def authenticate(self, credentials: Credentials) -> Token:
        self.linked_user_db.token = self.rpc('authenticate', credentials)
        return self.linked_user_db.token

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token, token=token)

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(user_db)

    # Trying to get a user that does not exist should raise a KeyError
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Authentication token is required' in str(e)

    # Adding a novel user should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting a user that exists should work
    try:
        user_db.get_user('gciatto') == gc_user.copy(password=None)
    except RuntimeError as e:
        assert 'Authentication token is required' in str(e)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
            assert user_db.check_password(gc_cred) == True
            # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False

    # NEW TESTS
    new_user = User(
        username='pallax03',
        emails={'alex.mazzoni3@studio.unibo.it', 'alexmaz03@hotmail.it'},
        full_name='Alex Mazzoni',
        role=Role.USER,
        password='securepassword123',
    )

    user_db.add_user(new_user)

    token = auth_service.authenticate(Credentials('pallax03', 'securepassword123'))
    assert auth_service.validate_token(user_db.token) == True
    
    assert user_db.check_password(Credentials('pallax03', 'securepassword123')) == True
    
    try: 
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert "User pallax03 does not have required role ADMIN" in str(e)
        
    time.sleep(5)  # assuming token expiration time is set to 5 seconds in server
    
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert "Authentication token is expired" in str(e)
        
    auth_service.authenticate(gc_credentials_ok[0])  # authenticate as admin
    
    assert user_db.get_user('pallax03') == new_user.copy(password=None)
    assert user_db.get_user('gciatto') == gc_user.copy(password=None)