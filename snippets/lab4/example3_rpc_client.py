from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from typing import cast
import time

class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, *args, token: Token | None = None):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, token)
            print('# Marshalling', request, 'towards', "%s:%d" % client.remote_address)
            request = serialize(request)
            print('# Sending message:', request.replace('\n', '\n# '))
            client.send(request)
            response = client.receive()
            print('# Received message:', response.replace('\n', '\n# ')) # type: ignore
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

    def add_user(self, user: User, token: Token | None = None):
        self.rpc('add_user', user)

    def get_user(self, id: str, token: Token | None = None) -> User:
        user = self.rpc('get_user', id, token = token)
        assert isinstance(user, User)
        return cast(User, user)

    def check_password(self, credentials: Credentials, token: Token | None = None) -> bool:
        checked = self.rpc('check_password', credentials)
        assert isinstance(checked, bool)
        return bool(checked)
    
    
class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)
        
    def authenticate(self, credentials: Credentials, duration: timedelta | None = None) -> Token:
        token = self.rpc('authenticate', credentials, duration)
        assert isinstance(token, Token)
        return cast(Token, token)

    def validate_token(self, token: Token) -> bool:
        valid = bool(self.rpc('validate_token', token))
        assert isinstance(valid, bool)
        return bool(valid)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    server_address = address(sys.argv[1])
    user_db = RemoteUserDatabase(server_address)
    auth_service = RemoteAuthenticationService(server_address)

    # Trying to get a user that does not exist should raise a KeyError
    # try:
    #     user_db.get_user('gciatto')
    # except RuntimeError as e:
    #     assert 'User with ID gciatto not found' in str(e)

    # Adding a novel user should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting a user that exists should work
    # assert user_db.get_user('gciatto') == gc_user.copy(password=None)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False
    
    try: 
        auth_service.authenticate(gc_credentials_wrong)
    except RuntimeError as e:
        assert 'Invalid credentials' in str(e)
        
    for credentials in gc_credentials_ok:
        token = auth_service.authenticate(credentials, timedelta(days = 1))
        assert  auth_service.validate_token(token) == True
    
    token_expired = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds = 10))
    time.sleep(0.1)
    assert  auth_service.validate_token(token_expired) == False