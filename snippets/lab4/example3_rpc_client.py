from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from snippets.lab4.users import Token


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

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)

class RemoteUserAuth(RemoteUserDatabase, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)
        self.__token = None

    def get_user(self, user: User, metadata=None):
        if metadata and isinstance(metadata, Token):
            self.__token = metadata
        return self.rpc('get_user', user, metadata=self.__token)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        self.__token = self.rpc('authenticate', credentials, duration)
        return self.__token
    
    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)
    
    def check_privileges(self, db: UserDatabase, credentials: Credentials, token: Token) -> bool:
        if not db.check_password(credentials):
            raise ValueError("Invalid credentials")

        if not self.validate_token(token):
            raise ValueError("Invalid token")

        if token.user.role != Role.ADMIN:
            raise ValueError("You must be Admin to perform this operation")
    

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong, gc_user_hidden_password
    import sys
    import time

    user_auth = RemoteUserAuth(address(sys.argv[1]))

    # Adding a novel user should work
    user_auth.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_auth.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Trying to get a user without authentication should raise a PermissionError
    try:
        user_auth.get_user('gciatto')
    except RuntimeError as e:
        assert str(e).startswith("You are not")

    # Authenticating with correct credentials should work
    gc_token = user_auth.authenticate(gc_credentials_ok[0])

    # The token should contain the user without the password
    assert gc_token.user == gc_user_hidden_password

    # The token should expire in the future
    assert gc_token.expiration > datetime.now()

    # And should be valid
    assert user_auth.validate_token(gc_token) == True

    # Getting a user that exists while authenticated should work
    assert user_auth.get_user('gciatto') == gc_user.copy(password=None)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_auth.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_auth.check_password(gc_credentials_wrong) == False

    # Authenticating with wrong credentials should raise an error
    try:
        user_auth.authenticate(gc_credentials_wrong)
    except RuntimeError as e:
        assert 'Invalid credentials' in str(e)

    # A token with wrong signature should be invalid
    gc_token_wrong_signature = gc_token.copy(signature='example signature')
    assert user_auth.validate_token(gc_token_wrong_signature) == False

    # A token with expiration in the past should be invalid
    gc_token_expired = user_auth.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
    time.sleep(0.1)
    assert user_auth.validate_token(gc_token_expired) == False