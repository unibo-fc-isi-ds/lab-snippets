from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response, TokenHandler, TOKENS_FOLDER


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, token=None, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata=token)
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
        return self.rpc('add_user', None, user)

    def get_user(self, id: str, token: Token) -> User:
        return self.rpc('get_user', token, id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', None, credentials)
    
    def authenticate(self, credentials: Credentials) -> User:
        return self.rpc('authenticate', None, credentials)
    
    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', None, token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_user2, gc_credentials_ok, gc_credentials_wrong
    import sys, os


    user_db = RemoteUserDatabase(address(sys.argv[1]))

    # Trying to get a user that does not exist should raise a error
    try:
        user_db.get_user('gciatto', None)
    except RuntimeError as e:
        assert 'Token required' in str(e)

    # Adding a novel user should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')
    
    # Authentication should provide a valid token for the user
    token = user_db.authenticate(Credentials(gc_user.username, gc_user.password))
    assert token is not None
    assert user_db.validate_token(token) == True
    # Uses TokenHandler to save token
    TokenHandler.store(token)
    
    # Getting a user that exists should work
    assert user_db.get_user('gciatto', token) == gc_user.copy(password=None)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False
    
    # Load expired token from file
    expired_token = TokenHandler.load(TOKENS_FOLDER + 'token_expired.json')
    assert expired_token is not None
    
    # Validate token should fail
    assert user_db.validate_token(expired_token) == False
    
    # Load expired token from file
    wrong_token = TokenHandler.load(TOKENS_FOLDER + 'token_wrong.json')
    assert wrong_token is not None
    
    # Validate token should fail
    assert user_db.validate_token(wrong_token) == False
    
    # Adding new user with role user
    try:
        user_db.add_user(gc_user2)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')
    
    token = user_db.authenticate(Credentials(gc_user2.username, gc_user2.password))
    assert token is not None
    assert user_db.validate_token(token) == True
    # Reading users information from user2 should fail
    try:
        user_db.get_user('gciatto', token)
    except RuntimeError as e:
        assert 'Unauthorized' in str(e)