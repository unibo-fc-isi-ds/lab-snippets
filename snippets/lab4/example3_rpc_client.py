from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        """
        Initialize the client with the server address.
        """
        self.__server_address = address(*server_address)
        self.token = None  # Token for authentication, to be set when needed

    def rpc(self, name, *args):
        """
        Perform a remote procedure call to the server and handle the response.
        """
        client = Client(self.__server_address)
        try:
            print(f'# Connected to {client.remote_address[0]}:{client.remote_address[1]}')
            request = Request(name, args, self.token)  # Include token in the request if available
            print(f'# Marshalling {request} towards {client.remote_address[0]}:{client.remote_address[1]}')
            request = serialize(request)
            print(f'# Sending message: {request.replace("\n", "\n# ")}')
            client.send(request)
            response = client.receive()
            print(f'# Received message: {response.replace("\n", "\n# ")}')
            response = deserialize(response)
            assert isinstance(response, Response)
            print(f'# Unmarshalled {response} from {client.remote_address[0]}:{client.remote_address[1]}')
            if response.error:
                raise RuntimeError(response.error)
            return response.result
        finally:
            client.close()
            print(f'# Disconnected from {client.remote_address[0]}:{client.remote_address[1]}')


class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        """
        Initialize the RemoteUserDatabase with server address.
        """
        super().__init__(server_address)

    def add_user(self, user: User):
        """
        Add a user to the remote database.
        """
        return self.rpc('add_user', user)

    def get_user(self, id: str, token: Token) -> User:
        """
        Get a user by ID from the remote database, with token authentication.
        """
        self.token = token  # Set the token for authentication
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        """
        Check the password for given credentials in the remote database.
        """
        return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub):
    def __init__(self, server_address):
        """
        Initialize the RemoteAuthenticationService with server address.
        """
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials):
        """
        Authenticate a user using their credentials.
        """
        return self.rpc('authenticate', credentials)

    def validate(self, token: Token) -> bool:
        """
        Validate a token on the server.
        """
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    # Initialize the RemoteUserDatabase with the server address
    user_db = RemoteUserDatabase(address(sys.argv[1]))

    # Trying to get a user that does not exist should raise a RuntimeError
    try:
        user_db.get_user('gciatto', token=None)  # No token provided, so should raise an error
    except RuntimeError as e:
        assert 'User with ID gciatto not found' in str(e)

    # Adding a novel user should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exists should raise a RuntimeError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting a user that exists should work
    assert user_db.get_user('gciatto', token=None) == gc_user.copy(password=None)

    # Checking credentials should work if the password is correct
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False
