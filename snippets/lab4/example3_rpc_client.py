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

    def get_user(self, id: str, token: Token) -> User:
        self.token = token
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)

class AuthenticationClientStub(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)
    
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        return self.rpc('authenticate', credentials, duration)

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)

class ClientStubFull:
    def __init__(self, server_address):
        self.remote = RemoteUserDatabase(server_address)
        self.auth = AuthenticationClientStub(server_address)

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys


    client_stub = ClientStubFull(address(sys.argv[1])) #RemoteUserDatabase(address(sys.argv[1]))

    # Trying to get a user that does not exist should raise a KeyError
    try:
        client_stub.remote.get_user('gciatto')
    except RuntimeError as e:
        assert 'User with ID gciatto not found' in str(e)

    # Adding a novel user should work
    client_stub.remote.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        client_stub.remote.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')