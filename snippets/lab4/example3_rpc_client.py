from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response

# General ClientStub class
class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)
        self.token: Token = None                                       # Memorize token of authenticated user

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata = self.token)       # Passing Token in request as metadata
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

# Specific stub: Implementation of the UserDatabase interface
class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


# Specific stub: Implementation of the AuthenticationService interface
class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        token = self.rpc('authenticate', credentials, duration)
        self.token = token                          # Token is memorized
        return token

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong, gc_user_hidden_password
    import sys
    from datetime import datetime, timedelta
    import time

    ga_user = User(
        username='ga',
        emails={'ga@unibo.it'},
        full_name='G.A.',
        role=Role.USER,
        password='my secret password',
    )
    ga_credentials_ok = [Credentials(id, ga_user.password) for id in ga_user.ids]


    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(address(sys.argv[1]))

    print("\n*******************************************")
    print("*** SECURE AUTHENTICATION SERVICE TESTS ***")
    print("*******************************************\n")

    # Fails: no user in db
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Authentication failed:' in str(e)

    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Fails: no token provided
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert 'Authentication failed:' in str(e)

    token = auth_service.authenticate(gc_credentials_ok[0])
    user_db.token = token 
    assert auth_service.validate_token(user_db.token) == True

    # Success: token is valid, user is ADMIN
    try:
        retrieved_user = user_db.get_user('gciatto')
        assert user_db.get_user('gciatto') == gc_user.copy(password=None)
    except RuntimeError as e:
        print(f"Error: {e}")

    # Add user with Role.USER
    try:
        user_db.add_user(ga_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')
    token = auth_service.authenticate(ga_credentials_ok[0])
    user_db.token = token 

    # Fails: token is valid, user is USER
    try:
        retrieved_user = user_db.get_user('ga')
        assert user_db.get_user('ga') == gc_user.copy(password=None)
    except RuntimeError as e:
        print(f"Error: {e}")






    """ USER DATABASE TESTS """
    """ print("\n*********************")
    print("*** USER DB TESTS ***")
    print("*********************\n")
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
    assert user_db.check_password(gc_credentials_wrong) == False """


    """ AUTHENTICATION SERVICE TESTS """
    """ print("\n************************************")
    print("*** AUTHENTICATION SERVICE TESTS ***")
    print("************************************\n")

    # Authenticating with wrong credentials should raise a ValueError
    try:
        auth_service.authenticate(gc_credentials_wrong)
    except RuntimeError as e:
        assert 'Invalid credentials' in str(e)

    # Authenticating with correct credentials should work
    gc_token = auth_service.authenticate(gc_credentials_ok[0])
    # The token should contain the user, but not the password
    assert gc_token.user == gc_user_hidden_password
    # The token should expire in the future
    assert gc_token.expiration > datetime.now()

    # A genuine, unexpired token should be valid
    assert auth_service.validate_token(gc_token) == True

    # A token with wrong signature should be invalid
    gc_token_wrong_signature = gc_token.copy(signature='wrong signature')
    assert auth_service.validate_token(gc_token_wrong_signature) == False

    # A token with expiration in the past should be invalid
    gc_token_expired = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
    time.sleep(0.1)
    assert auth_service.validate_token(gc_token_expired) == False """