from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self._server_address = address(*server_address)
        self.token = None

    def rpc(self, name, *args):
        client = Client(self._server_address)
        try:
            print(f'# Connected to {client.remote_address[0]}:{client.remote_address[1]}')
            request = Request(name, args, self.token)
            print(f'# Marshalling request: {request} towards {client.remote_address}')
            serialized_request = serialize(request)
            print(f'# Sending message:\n{serialized_request.replace("\n", "\n# ")}')
            client.send(serialized_request)
            
            response_message = client.receive()
            print(f'# Received message:\n{response_message.replace("\n", "\n# ")}')
            response = deserialize(response_message)
            if not isinstance(response, Response):
                raise RuntimeError("Invalid response format received.")
            print(f'# Unmarshalled response: {response} from {client.remote_address}')

            if response.error:
                raise RuntimeError(response.error)
            return response.result
        finally:
            client.close()
            print(f'# Disconnected from {client.remote_address[0]}:{client.remote_address[1]}')


class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, user_id: str, token: Token) -> User:
        self.token = token
        return self.rpc('get_user', user_id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials):
        return self.rpc('authenticate', credentials)

    def validate(self, token: Token) -> bool:
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    server_addr = address(sys.argv[1])
    user_db = RemoteUserDatabase(server_addr)

    # Test cases
    try:
        # Attempting to get a non-existing user should raise a KeyError
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'User with ID gciatto not found' in str(e)

    # Adding a new user should work
    user_db.add_user(gc_user)

    # Adding an already existing user should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting an existing user should work
    retrieved_user = user_db.get_user('gciatto', None)
    assert retrieved_user == gc_user.copy(password=None)

    # Valid credentials should return True
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) is True

    # Invalid credentials should return False
    assert user_db.check_password(gc_credentials_wrong) is False
