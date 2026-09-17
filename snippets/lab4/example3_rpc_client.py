from typing import Any
from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from snippets.lab4.example2_rpc_server import admin_user
from snippets.lab4.users import Token


class ClientStub:
    def __init__(self, server_address: tuple[str, int], token: Token | None):
        self.__server_address = address(*server_address)
        self.__token = token

    def update_token(self, token: Token | None): 
        self.__token = token

    def rpc(self, name, *args) -> Any:
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, self.__token)
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
    def __init__(self, server_address, token: Token | None):
        super().__init__(server_address, token)

    def add_user(self, user: User):
        return self.rpc('db/add_user', user)

    def get_user(self, id: str) -> User:
        return self.rpc('db/get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('db/check_password', credentials)


class RemoteUserAuthentication(ClientStub, AuthenticationService): 

    def __init__(self, server_address: tuple[str, int]):
        super().__init__(server_address, None)

    def authenticate(self, credentials: Credentials, duration: timedelta | None = None) -> Token:
        result =  self.rpc('auth/authenticate', credentials, duration)
        if not isinstance(result, Token):
            raise ValueError("Got invalid response")
        return result

    def validate_token(self, token: Token) -> bool:
        result = self.rpc('auth/validate_token', token)
        if not isinstance(result, bool):
            raise ValueError("Got invalid response")
        return result


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys
    addr = address(sys.argv[1])
    user_db = RemoteUserDatabase(addr, None)

    try:
        # If we are not authenticated, we cannot add a user
        user_db.add_user(gc_user)
        assert False, ""
    except RuntimeError as e:
        assert "unauthenticated" in str(e).lower()

    auth = RemoteUserAuthentication(addr)
    assert admin_user.password is not None

    # Authenticate using admin user
    token = auth.authenticate(Credentials(admin_user.username, password=admin_user.password))
    user_db.update_token(token)

    # Trying to get a user that does not exist should raise a KeyError
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        print(e)
        assert 'User with ID gciatto not found' in str(e)

    

    # Adding a novel user should now work as we are authenticated
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
