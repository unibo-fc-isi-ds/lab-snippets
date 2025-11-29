from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server): # RPC server stub --> caso particolare di server
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase() #inizializziamo una nuova istanza del database utenti in memoria
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
    
    def __handle_request(self, request):
        #request.name = get_user | add_user | check_password
        #sono le tre funzioni del database utenti
        try:
            method = getattr(self.__user_db, request.name) #es. self.__user_db.add_user
            #gettattr --> prende in input un oggetto e una stringa che rappresenta il nome di un attributo
            #restituisce (se esiste) l'attributo dell'oggetto con quel nome
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)


if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
        
    server.close()
