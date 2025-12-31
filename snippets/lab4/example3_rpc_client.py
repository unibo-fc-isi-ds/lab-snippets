from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args)
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

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str, token: Token) -> User:
        # get_user è ristretta ad utenti admin
        return self.rpc('get_user', id, token)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials) -> Token:
        return self.rpc('authenticate', credentials)

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)



if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_user_hidden_password, gc_credentials_ok, gc_credentials_wrong
    import sys


    user_db = RemoteUserDatabase(address(sys.argv[1]))

    # Adding a novel user (ADMIN) should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # --- Authentication service (remote) ---
    auth_service = RemoteAuthenticationService(address(sys.argv[1]))

    # Authenticate as ADMIN to get an authorization token
    admin_token = auth_service.authenticate(gc_credentials_ok[0])

    # Getting a user that exists should work (admin-only)
    assert user_db.get_user('gciatto', admin_token) == gc_user.copy(password=None)

    # Trying to get a user that does not exist should raise a KeyError (admin-only)
    try:
        user_db.get_user('does-not-exist', admin_token)
    except RuntimeError as e:
        assert 'User with ID does-not-exist not found' in str(e)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False

    # Authenticating with wrong credentials should raise a RuntimeError
    try:
        auth_service.authenticate(gc_credentials_wrong)
    except RuntimeError as e:
        assert 'Invalid credentials' in str(e)

    # Authenticating with correct credentials should work
    token = auth_service.authenticate(gc_credentials_ok[0])
    assert isinstance(token, Token)
    assert token.user == gc_user_hidden_password
    assert token.expiration > datetime.now()
    assert auth_service.validate_token(token) == True

