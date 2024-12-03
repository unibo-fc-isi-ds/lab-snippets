from snippets.lab3 import Client, address
from snippets.lab4.users import *
from datetime import timedelta, datetime
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)
        self.__token = None

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata=self.__token)
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
    
    def authenticate(self, credentials: Credentials, expiration: timedelta) -> Token:
        token = self.rpc('authenticate', credentials, expiration)
        self.__token = token  # 保存 token 以供后续使用
        return token

    def set_token(self, token: Token):
        self.__token = token

    def get_saved_token(self):
        return self.__token

# for excercise 4-01  # for excercise 4-02
class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, expiration: datetime) -> Token:
        token = self.rpc('authenticate', credentials, expiration)
        self.set_token(token)  # 保存 Token
        return token

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)
    
# for exercise 4-02
class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address,  auth_service: RemoteAuthenticationService):
        super().__init__(server_address)
        self.auth_service = auth_service
        

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
        token = self.auth_service.get_saved_token()
        print('----------------get_user_token----------------')
        print(token)
        if token is None:
            raise ValueError("Token is required")
        self.set_token(token)
        print('111111111')
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys


    user_db = RemoteUserDatabase(address(sys.argv[1]))

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
    assert user_db.get_user('gciatto') == gc_user.copy(password=None)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False
