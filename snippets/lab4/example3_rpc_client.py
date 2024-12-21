from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)
        d = datetime.min
        self.token = None

    def rpc(self, name, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            if self.token is not None:
                request = Request(name, args, self.token)
            else:
                request = Request(name,args)
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
            if isinstance(response.result,Token):
                self.token = response.result
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
    

class RemoteAuthtenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)
    
    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token',token)
    
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        return self.rpc('authenticate',credentials)
   

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong, user_list
    import sys


    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth = RemoteAuthtenticationService(address(sys.argv[1]))

    # Trying to get a user that does not exist should raise a KeyError
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert str(e).startswith("Request rejected:")

    # Adding a novel user should work
    for user in user_list:
        user_db.add_user(user)

    # Trying to add a user that already exist should raise a ValueError
    try:
        user_db.add_user(gc_user)
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Getting a user that exists should work but not if not authenticated
    try:
        assert user_db.get_user('gciatto') == gc_user.copy(password=None)
    except RuntimeError as e:
        assert str(e).startswith("Request rejected:")

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    try:
        for gc_cred in gc_credentials_ok:
            user_db.check_password(gc_cred)
    except RuntimeError as e:
        assert str(e).startswith("Request rejected:")
    
    # Checking credentials should fail if the password is wrong
    #assert user_db.check_password(gc_credentials_wrong) == False
    
    # Should work
    auth.token = user_db.token = auth.authenticate(gc_credentials_ok[0])
    # Check the token validation
    assert auth.validate_token(user_db.token) == True
    
    try:
        user_db.get_user('gciatto')
    except RuntimeError as e:
        assert str(e).startswith("Request rejected:")
        

    
        
    
    
    
    
    
