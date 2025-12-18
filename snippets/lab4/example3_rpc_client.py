from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)
        self.current_token: Token = None

    def rpc(self, name, *args, metadata=None):
        client = Client(self.__server_address)
        try:
            if metadata is None:
                metadata = self.current_token
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args=args, metadata=metadata)
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

    def get_user(self, id: str, metadata: Token = None) -> User:
        return self.rpc('get_user', id, metadata=metadata)

    def check_password(self, credentials: Credentials, metadata: Token = None) -> bool:
        return self.rpc('check_password', credentials, metadata=metadata)
    
class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)
        
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        token = self.rpc('authenticate', credentials, duration)
        self._current_token = token
        return token

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
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

    # Trying to get a user that exists without authentication should raise a KeyError
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Missing token' in str(e)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False
    
    print("-------------------------------------------------")
    
    # --- Authentication tests ---
    from datetime import timedelta, datetime
    from snippets.lab4.example1_presentation import serialize, deserialize

    # Authenticate with valid credentials should return a token
    for gc_cred in gc_credentials_ok:
        token = auth_service.authenticate(gc_cred, timedelta(seconds=10))
        user_db.current_token = token
        user = user_db.get_user('gciatto') # the saved token should be loaded automatically by the client
        assert user.username == 'gciatto'
        assert auth_service.validate_token(token) == True

    # Token expiration test
    token = auth_service.authenticate(gc_credentials_ok[0], timedelta(seconds=1))
    user_db.current_token = token
    assert auth_service.validate_token(user_db.current_token) == True
    
    # Wait for token to expire
    import time
    time.sleep(1.5)
    assert auth_service.validate_token(user_db.current_token) == False

    # Test serialization/deserialization of token
    token = auth_service.authenticate(gc_credentials_ok[0], timedelta(days=1))
    user_db.current_token = token
    serialized_token = serialize(token)
    deserialized_token = deserialize(serialized_token)
    assert auth_service.validate_token(deserialized_token) == True
    
    print("ALL TESTS PASSED")
    
