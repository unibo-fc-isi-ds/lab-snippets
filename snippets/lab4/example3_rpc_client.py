import time

from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)
        self.token = None

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, self.token)
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

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        self.token = self.rpc('authenticate', credentials, duration)
        return self.token

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_admin, gn_user, gc_credentials_ok, gc_credentials_wrong, \
    gc_user_hidden_password, gn_credentials_ok
    import sys

    remote_endpoint = address(sys.argv[1])
    user_db = RemoteUserDatabase(remote_endpoint)
    auth_service = RemoteAuthenticationService(remote_endpoint)

    # Register user with ADMIN role
    user_db.add_user(gc_admin)
    # Register user with USER role
    user_db.add_user(gn_user)

    # Authenticate ADMIN
    user_db.token = auth_service.authenticate(gc_credentials_ok[0])
    assert auth_service.validate_token(user_db.token) is True

    # Check that ADMIN can get USER
    user_db.get_user('gnardicchia')

    # Authenticate USER
    user_db.token = auth_service.authenticate(gn_credentials_ok[0])
    assert auth_service.validate_token(user_db.token) is True

    # Check that USER cannot get ADMIN
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Admin privileges required' in str(e)

    # Trying to get a user that does not exist should raise a RuntimeError
    user_db.token = auth_service.authenticate(gc_credentials_ok[0])
    try:
        user_db.get_user('user')
    except RuntimeError as e:
        assert 'User with ID user not found' in str(e)

    # Trying to add a user that already exist should raise a RuntimeError
    try:
        user_db.add_user(gc_admin)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting a user that exists should work (with ADMIN role)
    assert user_db.get_user('gciatto') == gc_admin.copy(password=None)

    # Checking credentials should work if there exists a user with the same ID and password
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) is True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) is False

    # Authenticating with wrong credentials should raise a RuntimeError
    try:
        auth_service.authenticate(gc_credentials_wrong)
    except RuntimeError as e:
        assert 'Invalid credentials' in str(e)

    # Authenticating with correct credentials should work
    user_db.token = auth_service.authenticate(gc_credentials_ok[0])
    # The token should contain the user, but not the password
    assert user_db.token.user == gc_user_hidden_password
    # The token should expire in the future
    assert user_db.token.expiration > datetime.now()

    # A genuine, unexpired token should be valid
    assert auth_service.validate_token(user_db.token) is True

    # A token with wrong signature should be invalid
    gc_token_wrong_signature = user_db.token.copy(signature='wrong signature')
    assert auth_service.validate_token(gc_token_wrong_signature) is False

    # A token with expiration in the past should be invalid
    user_db.token = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
    time.sleep(0.1)
    try:
        auth_service.validate_token(user_db.token)
    except RuntimeError as e:
        assert 'Invalid or missing token' in str(e)