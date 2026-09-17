from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import time

class TokenStorage:
    """Shared token storage across all client stubs"""
    _tokens = {}  # Dictionary mapping server_address -> token

    @classmethod
    def set_token(cls, server_address: tuple, token: Token):
        cls._tokens[server_address] = token

    @classmethod
    def get_token(cls, server_address: tuple) -> Token | None:
        return cls._tokens.get(server_address)

    @classmethod
    def clear_token(cls, server_address: tuple):
        if server_address in cls._tokens:
            del cls._tokens[server_address]

class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def set_token(self, token: Token):
        TokenStorage.set_token(self.__server_address, token)

    def get_token(self) -> Token | None:
        return TokenStorage.get_token(self.__server_address)

    def clear_token(self):
        TokenStorage.clear_token(self.__server_address)

    def rpc(self, name, *args, require_auth=False):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)

            metadata = {}
            token = self.get_token()
            if require_auth and token:
                metadata['token'] = {
                    'user': token.user,
                    'expiration': token.expiration,
                    'signature': token.signature
                }

            request = Request(name, args, metadata)
            print('# Marshalling', request.name, 'towards', "%s:%d" % client.remote_address)
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
        return self.rpc('get_user', id, require_auth=True)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        """Authenticate user and return a token"""
        token = self.rpc('authenticate', credentials, duration)
        self.set_token(token)
        return token

    def validate_token(self, token: Token) -> bool:
        """Validate an authentication token"""
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(address(sys.argv[1]))

    print("Testing Secure RPC-based UserDatabase and Authentication Service")

    print("\n1.Testing get non-existent user without authentication")
    try:
        user_db.get_user('gciatto')
        print("   Should have failed without authentication")
    except RuntimeError as e:
        if 'Authentication required' in str(e) or 'missing token' in str(e):
            print("   Correctly rejected unauthenticated request")
        else:
            print(f"   Unexpected error: {e}")

    print("\n2.Adding new user")
    user_db.add_user(gc_user)
    print("   User added successfully (no auth required)")

    print("\n3.Testing add duplicate user")
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        print("   Correctly rejected duplicate user")

    print("\n4.Adding regular user")
    regular_user = User(
        username='regular',
        emails={'regular@example.com'},
        full_name='Regular User',
        role=Role.USER,
        password='regular_password'
    )
    user_db.add_user(regular_user)
    print("   Regular user added")

    print("\n5.Authenticating as regular user")
    regular_creds = Credentials('regular', 'regular_password')
    regular_token = auth_service.authenticate(regular_creds)
    print("   Authentication successful")
    print(f"   User role: {regular_token.user.role.name}")

    print("\n6.Testing get_user as regular user (not admin)")
    try:
        user_db.get_user('gciatto')
        print("   Should have failed (not admin)")
    except RuntimeError as e:
        if 'admin role required' in str(e) or 'Authorization failed' in str(e):
            print("   Correctly rejected non-admin request")

    print("\n7.Authenticating as admin user")
    admin_token = auth_service.authenticate(gc_credentials_ok[0])
    print("   Authentication successful")
    print(f"   User role: {admin_token.user.role.name}")

    print("\n8.Testing get_user as admin user")
    retrieved_user = user_db.get_user('gciatto')
    assert retrieved_user == gc_user.copy(password=None)
    print("   User retrieved successfully with admin token")

    print("\n9.Checking passwords (no auth required)")
    assert user_db.check_password(gc_credentials_ok[0]) == True
    assert user_db.check_password(gc_credentials_wrong) == False
    print("   Password checking works without authentication")

    print("\n10.Testing token validation")
    assert auth_service.validate_token(admin_token) == True
    print("   Admin token is valid")

    print("\n11.Testing with expired token")
    short_token = auth_service.authenticate(gc_credentials_ok[0], timedelta(seconds=1))
    print("   Waiting 2 seconds for token to expire")
    time.sleep(2)
    try:
        user_db.get_user('gciatto')
        print("   Should have failed with expired token")
    except RuntimeError as e:
        if 'expired' in str(e).lower() or 'Invalid' in str(e):
            print("   Correctly rejected expired token")

    print("\n12.Testing with tampered token")
    tampered_token = admin_token.copy(signature="tampered_signature")
    user_db.set_token(tampered_token)
    try:
        user_db.get_user('gciatto')
        print("   Should have failed with tampered token")
    except RuntimeError as e:
        if 'Invalid' in str(e) or 'expired' in str(e):
            print("   Correctly rejected tampered token")

    print("\nAll tests completed successfully!")