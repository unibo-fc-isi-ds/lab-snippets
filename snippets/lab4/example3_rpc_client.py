from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response

# questo è il famoso ClientStub, che fa exploit di TCP Client "under the hood"
class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address)

    # creo qua dentro il Client, che contatterà il server di certo indirizzo. Farà
    # poi lui la connessione creando una request passando il nome della funzione e gli argomenti.
    def rpc(self, name, serviceType, *args):
        client = Client(self.__server_address)
        try:
            print('# Connected to %s:%d' % client.remote_address)
            # creo qui la Request, specificando il suo nome, il tipo di Servizio e gli argomenti 
            request = Request(name, serviceType, args)
            # anche qui dopo che il Client ha creato la request, faccio marshall del messaggio
            print('# Marshalling', request, 'towards', "%s:%d" % client.remote_address)
            request = serialize(request)
            print('# Sending message:', request.replace('\n', '\n# '))
            # invio la richiesta al Server e la ricevo, facendo poi Unmarshall
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


# anche in questo caso implemento l'interfaccia UserDatabase
class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)

    # in questo caso l'implementazione viene fatta usando la funzione rpc passandogli argomenti necessari (nome funzione, tipo di servizio, argomenti)
    def add_user(self, user: User):
        return self.rpc('add_user', 'databaseService',user)

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', 'databaseService',id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', 'databaseService', credentials)

# creo una nuova classe chiamata RemoteAuthenticationService che utilizza un ClientStub e un AuthenticationService
class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)

    # definisco qui il metodo authenticate e il metodo di validazione del token
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        return self.rpc('authenticate', 'authenticationService', credentials, duration)

    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', 'authenticationService', token)


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
