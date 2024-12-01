from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import os

FILEAUTH="auth.json"

class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    def rpc(self, name, authToken, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            request = Request(name, args, metadata=authToken)
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
            if isinstance(response.result, Token):
                writeFile(response.result)
                
            return response.result
        finally:
            client.close()
            print('# Disconnected from %s:%d' % client.remote_address)


class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)

    def add_user(self, user: User):
        return self.rpc('add_user', None, user)

    def get_user(self, id: str) -> User:
        t=readFile()
        return self.rpc('get_user', t, id)

    def check_password(self, credentials: Credentials) -> bool:
        t=readFile()
        return self.rpc('check_password', t, credentials)
    
    def authenticate(self, credentials: Credentials):
        t=self.rpc('authenticate', None, credentials)
        writeFile(t)
    
    def logout(self):
        if os.path.exists(FILEAUTH):
            os.remove(FILEAUTH)
            return "User logged out correctly"
        else:
            return "Error while logging out"



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


def writeFile(t:Token):
    if(t!=None):
        json_object = serialize(t)
        #write token to a file
        with open(FILEAUTH, "w") as outfile:
            outfile.write(json_object)
            print('# Authentication token saved')

def readFile()->Token:
    # Opening JSON file
    with open(FILEAUTH, 'r') as openfile:
    # Reading from json file
        json_string = openfile.read() #string containing Token is read
        json_object=deserialize(json_string) #token is parsed into a Token object
        if isinstance(json_object, Token):
            print('# Authentication token read')
            return json_object
        