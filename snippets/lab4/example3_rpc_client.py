import sys
import os

from snippets.lab4.users.impl import _compute_sha256_hash
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print(f"# Connected to {self.__server_address}")
            request = Request(name=name, args=args)
            print("# Marshalling request:", request)
            serialized_request = serialize(request)
            print("# Sending serialized request:", serialized_request)
            client.send(serialized_request)
            
            # Wait for the server's response
            response = client.receive()
            if response is None:
                raise RuntimeError("No response received from server")
            print("# Received serialized response:", response)
            deserialized_response = deserialize(response)
            print("# Deserialized response:", deserialized_response)
            
            if deserialized_response.error:
                raise RuntimeError(deserialized_response.error)
            return deserialized_response.result
        finally:
            client.close()
            print("# Disconnected from", self.__server_address)

class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def authenticate(self, credentials: Credentials, duration: timedelta = None):
        return self.rpc('authenticate', credentials, duration)


    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)


class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)

    def add_user(self, user: User):
        print(f"Attempting to add user: {user}")
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
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
