from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server): # RPC server stub --> caso particolare di server
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase() #inizializziamo una nuova istanza del database utenti in memoria
        self.__auth_service = InMemoryAuthenticationService(self.__user_db) #inizializziamo il servizio di autenticazione in memoria
        # self.__user_db.add_user(u) #opzionale: aggiungiamo un utente di test
        # self.__user_db.get_user(id) --> user #opzionale: aggiungiamo le credenziali di test
        # self.__user_db.check_password(creds) --> bool

    #callback per la gestione degli eventi di connessione
    def __on_connection_event(self, event, connection, address, error):
        match event:
            case 'listen':
                print('Server listening on %s:%d' % address)
            case 'connect':
                connection.callback = self.__on_message_event #attacco la callback per la gestione dei messaggi
            case 'error':
                traceback.print_exception(error)
            case 'stop':
                print('Server stopped')
    
    #callback per la gestione degli eventi di messaggio
    def __on_message_event(self, event, payload, connection, error):
        match event:
            case 'message':
                print('[%s:%d] Open connection' % connection.remote_address)
                request = deserialize(payload)
                assert isinstance(request, Request)
                print('[%s:%d] Unmarshall request:' % connection.remote_address, request)
                response = self.__handle_request(request)
                connection.send(serialize(response))
                print('[%s:%d] Marshall response:' % connection.remote_address, response)
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    
    #Metodo per gestire una richiesta RPC
    def __handle_request(self, request):
        #request.name = get_user | add_user | check_password (metodi di UserDatabase)
        #request.name = autenticate | validate_token (metodi di AuthenticationService)

        try:
            if request.service == 'AuthenticationService':
                method = getattr(self.__auth_service, request.name) #ottiene l'attributo di un oggetto (dato il nome come stringa)
            elif request.service == 'UserDatabase':
                method = getattr(self.__user_db, request.name)
            else: raise ValueError(f"Unknown service {request.service}")

            result = method(*request.args) #chiama il metodo con gli argomenti forniti 
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)

#argv[1] rappresenta la tupla ip:porta del server --> stub

if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
        
    server.close()
