from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import sys
from datetime import datetime, timedelta

class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)
        self.token = None

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata={'token': self.token} if self.token else None)
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

class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        token = self.rpc('authenticate', credentials, duration)
        self.token = token
        return token

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)

class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong, gc_user_hidden_password

    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(address(sys.argv[1]))

    print('----- Testing user database -----')
    # Trying to get a user that does not exist should raise a KeyError
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'User with ID gciatto not found' in str(e)

    # Adding a novel user should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting a user that exists should work
    assert user_db.get_user('gciatto') == gc_user_hidden_password

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False

    print('----- Testing authentication -----')
    # Authenticating with wrong credentials should raise a ValueError
    try:
        auth_service.authenticate(gc_credentials_wrong)
    except RuntimeError as e:
        assert 'Invalid credentials' in str(e)

    # Authenticating with correct credentials should work
    gc_token = auth_service.authenticate(gc_credentials_ok[0])
    # The token should contain the user, but not the password
    assert gc_token.user == gc_user_hidden_password
    # The token should expire in the future
    assert gc_token.expiration > datetime.now()

    # This token should be valid
    assert auth_service.validate_token(gc_token) == True

    # A token with wrong signature should be invalid
    gc_token_wrong_signature = gc_token.copy(signature='wrong signature')
    assert auth_service.validate_token(gc_token_wrong_signature) == False

    print('----- Testing authorization -----')
    # Authenticate as admin
    admin_token = auth_service.authenticate(gc_credentials_ok[0])
    user_db.token = admin_token
    assert user_db.get_user('gciatto') == gc_user_hidden_password

    # Create a non-admin user
    non_admin_user = User(
        username='rick',
        emails={'rick@mail.com'},
        full_name='Riccardo Mazzi',
        role=Role.USER,
        password='password123',
    )
    user_db.add_user(non_admin_user)
    non_admin_credentials = Credentials('rick@mail.com', 'password123')
    non_admin_token = auth_service.authenticate(non_admin_credentials)

    # Authenticate as non-admin and try to get user data
    user_db.token = non_admin_token
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Unauthorized access' in str(e)

    # Try to get user data without authentication
    user_db.token = None
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Invalid or expired token' in str(e)