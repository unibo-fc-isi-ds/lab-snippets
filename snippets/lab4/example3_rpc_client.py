from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import time


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args)
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


class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        """Authenticate user and return a token"""
        return self.rpc('authenticate', credentials, duration)

    def validate_token(self, token: Token) -> bool:
        """Validate an authentication token"""
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(address(sys.argv[1]))

    print("Testing RPC-based UserDatabase and Authentication Service")

    print("\n1.Testing get non-existent user")
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'User with ID gciatto not found' in str(e)
        print("   Correctly raised error for non-existent user")

    print("\n2.Adding new user")
    user_db.add_user(gc_user)
    print("   User added successfully")

    print("\n3.Testing add duplicate user")
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')
        print("   Correctly rejected duplicate user")

    print("\n4.Getting existing user")
    assert user_db.get_user('gciatto') == gc_user.copy(password=None)
    print("   User retrieved successfully")

    print("\n5.Checking correct passwords")
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True
    print("   All correct passwords verified")

    print("\n6.Checking wrong password")
    assert user_db.check_password(gc_credentials_wrong) == False
    print("   Incorrect password correctly rejected")

    print("\n7.Testing authentication with correct credentials")
    token = auth_service.authenticate(gc_credentials_ok[0])
    assert token.user == gc_user.copy(password=None)
    assert token.expiration > datetime.now()
    print("   Authentication successful")
    print(f"   Token signature: {token.signature[:20]}")
    print(f"   Token expires: {token.expiration}")

    print("\n8.Testing token validation")
    assert auth_service.validate_token(token) == True
    print("   Token is valid")

    print("\n9.Testing authentication with wrong credentials")
    try:
        auth_service.authenticate(gc_credentials_wrong)
        print("   Authentication should have failed")
    except RuntimeError as e:
        if "Invalid credentials" in str(e):
            print("   Authentication correctly rejected")

    print("\n10.Testing token with tampered signature")
    tampered_token = token.copy(signature="tampered_signature_12345")
    assert auth_service.validate_token(tampered_token) == False
    print("   Tampered token correctly rejected")

    print("\n11.Testing short-lived token (expires in 1 second)")
    short_token = auth_service.authenticate(gc_credentials_ok[0], timedelta(seconds=1))
    print("   Short token created")
    assert auth_service.validate_token(short_token) == True
    print("   Token valid before expiration")
    print("   Waiting 2 seconds for token to expire")
    time.sleep(2)
    assert auth_service.validate_token(short_token) == False
    print("   Token correctly invalidated after expiration")

    print("\n12.Testing authentication with email instead of username")
    token_email = auth_service.authenticate(Credentials('giovanni.ciatto@unibo.it', gc_user.password))
    assert token_email.user.username == gc_user.username
    print("   Authentication with email successful")

    print("All tests completed successfully!")