from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, *args, metadata: Token | None = None):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata=metadata)
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
        self.token: Token | None = None

    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id, metadata=self.token)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)
    
class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)
        
    def authenticate(self, credentials, duration = None):
        return self.rpc('authenticate', credentials, duration)

    def validate_token(self, token):
        return self.rpc('validate_token', token)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys


    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(address(sys.argv[1]))

    # Trying to get a user that does not exist should raise a KeyError
    try:
       user_db.get_user('gciatto')
    except RuntimeError as e:
        assert str(e) in ('User with ID gciatto not found', 'Authentication token required')

    # Adding a novel user should work
    user_db.add_user(gc_user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting a user that exists should work
    # assert user_db.get_user('gciatto') == gc_user.copy(password=None)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False
    
    #############
    # NEW TESTS #
    #############
    
    # Unauthenticated access. Attempting to get information about a user without a token will raise a PermissionError
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert str(e) in ('Authentication token required')
    
    # Authenticating with the correct credentials should work
    token = auth_service.authenticate(gc_credentials_ok[0])
    
    # Store the token in the RemoteUserDatabase
    user_db.token = token
    
    # Attempting to get information about the user should work because the enquirer (gciatto) is both authenticated and authorized
    user_db.get_user('gciatto')
    
    # A new user who is not an ADMIN
    mr_user = User(
        username='mrossi',
        emails={'mario.rossi@unibo.it', 'mario.rossi@gmail.com'},
        full_name='Mario Rossi',
        role=Role.USER,
        password='my secret password',
    )
    
    mr_credentials_ok = [Credentials(id, mr_user.password) for id in mr_user.ids] # type: ignore
    
    # Adding a new user should work
    user_db.add_user(mr_user)
    
    # Authenticating with the correct credentials should work
    token = auth_service.authenticate(mr_credentials_ok[0])
    
    # Store the token in the RemoteUserDatabase
    user_db.token = token
    
    # Attempting to get information about both users should NOT work because the enquirer (mrossi) is authenticated but not authorized (USER)
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert str(e) in ('Admin role required')
        
    try:
        user_db.get_user('mrossi')
    except RuntimeError as e:
        assert str(e) in ('Admin role required')
    
    # Tampering with the token will be detected
    import copy
    tampered_token = copy.deepcopy(token)
    # Attempting to give 'mrossi' admin rights
    tampered_token.user.role = Role.ADMIN
    user_db.token = tampered_token
    
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert str(e) in ('Invalid token')
    
    # As expected, the user 'gciatto' is able to get information about anyone since he is authorized
    # Subsequent action do not require the token again since it's saved in the client
    token = auth_service.authenticate(gc_credentials_ok[0])
    user_db.token = token
    user_db.get_user('gciatto')
    user_db.get_user('mrossi')