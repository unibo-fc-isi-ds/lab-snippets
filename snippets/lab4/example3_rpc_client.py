from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response

# Implementazione del client RPC
# Si occupa di marshallare e unmarshallare le richieste e risposte
# e di gestire la connessione con il server RPC
class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        self.__server_address = address(*server_address) #transforma in tupla (ip, port)

    # Metodo generico per effettuare una chiamata di procedura remota
    def rpc(self, service, name, *args, authentication_token = None):
        client = Client(self.__server_address) #crea un client TCP che si connette al server all'indirizzo specificato
        try:
            print('# Connected to %s:%d' % client.remote_address) 
            request = Request(service, name, args, authentication_token) #creo un istanza di Request con il nome del metodo e gli argomenti
            print('# Marshalling', request, 'towards', "%s:%d" % client.remote_address)
            request = serialize(request) #la serializzo in stringa (ricorda : obj -> AST -> stringa)
            print('# Sending message:', request.replace('\n', '\n# '))
            client.send(request) #invio la richiesta serializzata al server
            response = client.receive() #aspetto la risposta dal server (bloccante)
            print('# Received message:', response.replace('\n', '\n# ')) #stampo la risposta ricevuta
            response = deserialize(response) #deserializzo la risposta (ricorda: stringa -> AST -> obj)
            assert isinstance(response, Response) #controllo che la risposta sia di tipo Response
            print('# Unmarshalled', response, 'from', "%s:%d" % client.remote_address)
            if response.error: #se c'è un errore nella risposta, lo rilancio come eccezione
                raise RuntimeError(response.error)
            return response.result
        finally:
            client.close() #chiudo la connessione (indipendentemente da successo o fallimento)
            print('# Disconnected from %s:%d' % client.remote_address)

#Ricorda che python supporta l'ereditarietà multipla
#Qui implementiamo le funzioni add_user, get_user e check_password in modo remoto
class RemoteUserDatabase(ClientStub, UserDatabase):
    service = 'UserDatabase'

    def __init__(self, server_address):
        super().__init__(server_address) #fa riferimento al costruttore di ClientStub
    
    #mi appello al metodo rpc della superclasse ClientStub
    def add_user(self, user: User, authentication_token = None):
        return self.rpc(self.service , 'add_user', user, authentication_token = None)

    def get_user(self, id: str) -> User:
        return self.rpc(self.service, 'get_user', id, self._token)

    def check_password(self, credentials: Credentials, authentication_token = None) -> bool:
        return self.rpc(self.service, 'check_password', credentials, authentication_token = None)

#Qui implementiamo le funzioni authenticate e validate_token in modo remoto
class RemoteAuthenticationService(ClientStub, AuthenticationService):
    service = 'AuthenticationService'
    
    def __init__(self, server_address):
        super().__init__(server_address)

    def authenticate(self, credentials: Credentials, authentication_token = None) -> Token:
        return self.rpc(self.service,'authenticate', credentials, authentication_token = None)

    def validate_token(self, token: Token, authentication_token : str) -> bool:
        return self.rpc(self.service,'validate_token', token, authentication_token)

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
    import sys

    # Qua entra in gioco la distribuzione
    user_db = RemoteUserDatabase(address(sys.argv[1]))
    auth_service = RemoteAuthenticationService(address(sys.argv[1])) #utile per testare il servizio di autenticazione
    
    #Cercando di ottenere un utente che non esiste dovrebbe sollevare un RuntimeError
    try:
        user_db.get_user('gciatto') #non esiste ancora
    except RuntimeError as e:
        assert 'User with ID gciatto not found' in str(e)

    #Adesso aggiungiamo l'utente gciatto
    user_db.add_user(gc_user)

    #Provarsi ad aggiungere di nuovo lo stesso utente dovrebbe sollevare un RuntimeError
    try:
        user_db.add_user(gc_user) 
    except RuntimeError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    #Ottenere l'utente appena aggiunto dovrebbe funzionare
    assert user_db.get_user('gciatto') == gc_user.copy(password=None)

    # Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True

    # Checking credentials should fail if the password is wrong
    assert user_db.check_password(gc_credentials_wrong) == False
