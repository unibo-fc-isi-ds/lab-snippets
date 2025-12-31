import time
from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from typing import Optional
import os


def _build_token_file_path(user_id: str, file_path: str = None) -> str:
    """Construct absolute path to token file."""
    filename = file_path if file_path else f'{user_id}.json'
    return os.path.join(os.path.expanduser('~'), filename)


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, *args, metadata=None):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata=metadata)
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

    def get_user(self, id: str, token: Token = None) -> User:
        return self.rpc('get_user', id, metadata=token)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)

class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        return self.rpc('authenticate', credentials, duration)

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)

    @staticmethod
    def read_token(user_id: str, file_path: str = None) -> Token:
        """Read authentication token from filesystem."""
        full_path = _build_token_file_path(user_id, file_path)
        try:
            with open(full_path, 'r') as f:
                return deserialize(f.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot find token file at: {full_path}")

    @staticmethod
    def write_token(token: Token, user_id: str, file_path: str = None):
        """Write authentication token to filesystem."""
        full_path = _build_token_file_path(user_id, file_path)
        with open(full_path, 'w') as f:
            f.write(serialize(token))

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong, gc_user_hidden_password
    import sys


    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(address(sys.argv[1]))

    # Adding a novel user should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Authenticate to get a token for protected operations
    gc_token = auth_service.authenticate(gc_credentials_ok[0])

    # Getting a user requires authentication (admin token)
    assert user_db.get_user('gciatto', gc_token) == gc_user.copy(password=None)

    # Trying to get a user without token should fail
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Authentication required' in str(e)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False

    # Authenticating with wrong credentials should raise a ValueError
    try:
        auth_service.authenticate(gc_credentials_wrong)
    except RuntimeError as e:
        assert 'Invalid credentials' in str(e)

    # The token should contain the user, but not the password
    assert gc_token.user == gc_user_hidden_password
    # The token should expire in the future
    assert gc_token.expiration > datetime.now()

    # A genuine, unexpired token should be valid
    assert auth_service.validate_token(gc_token) == True

    # A token with wrong signature should be invalid
    gc_token_wrong_signature = gc_token.copy(signature='wrong signature')
    assert auth_service.validate_token(gc_token_wrong_signature) == False

    # A token with expiration in the past should be invalid
    gc_token_expired = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
    time.sleep(0.1)
    assert auth_service.validate_token(gc_token_expired) == False
