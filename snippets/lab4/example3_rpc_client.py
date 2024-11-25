from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)
        self.__auth_token = None  # Save the authentication token

    def set_auth_token(self, token: Token):
        """Set the client's authentication token"""
        self.__auth_token = token

    def rpc(self, name, *args):
        """Send an RPC request and return the result"""
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)

            # Prepare the request
            metadata = {'token': self.__auth_token} if self.__auth_token else {}
            request = Request(name, args, metadata)
            print('# Marshalling', request, 'towards', "%s:%d" % client.remote_address)

            # Serialize and send the request
            serialized_request = serialize(request)
            print('# Sending message:', serialized_request.replace('\n', '\n# '))
            client.send(serialized_request)

            # Receive and deserialize the response
            response = client.receive()
            if response is None:
                raise RuntimeError("No response received from the server.")
            print('# Received message:', response.replace('\n', '\n# '))
            response = deserialize(response)
            assert isinstance(response, Response)
            print('# Unmarshalled', response, 'from', "%s:%d" % client.remote_address)

            # Check for errors in the response
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
        """Remotely call the add_user method"""
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
        """Remotely call the get_user method"""
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        """Remotely call the check_password method"""
        return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        """Remotely call the authenticate method to obtain a token"""
        return self.rpc('authenticate', credentials, duration)

    def validate_token(self, token: Token) -> bool:
        """Remotely call the validate_token method to validate the token"""
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    # Create remote service instances
    server_address = address(sys.argv[1])
    user_db = RemoteUserDatabase(server_address)
    auth_service = RemoteAuthenticationService(server_address)

    try:
        # User-related operations
        # Attempt to get a non-existent user
        try:
            user_db.get_user('gciatto')
        except RuntimeError as e:
            assert 'User with ID gciatto not found' in str(e)

        # Add a new user
        user_db.add_user(gc_user)

        # Adding the same user again should return an error
        try:
            user_db.add_user(gc_user)
        except RuntimeError as e:
            assert str(e).startswith('User with ID')
            assert str(e).endswith('already exists')

        # Get an existing user
        assert user_db.get_user('gciatto') == gc_user.copy(password=None)

        # Verify credentials with correct password
        for gc_cred in gc_credentials_ok:
            assert user_db.check_password(gc_cred) is True

        # Verify credentials with incorrect password
        assert user_db.check_password(gc_credentials_wrong) is False

        # Authentication-related operations
        # Obtain a token using correct credentials
        gc_token = auth_service.authenticate(gc_credentials_ok[0])
        assert gc_token.user == gc_user.copy(password=None)
        assert gc_token.expiration > datetime.now()

        # Validate token validity
        assert auth_service.validate_token(gc_token) is True

        # Validate expired token
        expired_token = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
        import time
        time.sleep(0.1)
        assert auth_service.validate_token(expired_token) is False

    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
