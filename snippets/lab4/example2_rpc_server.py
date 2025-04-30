from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


# creo una classe ServerStub che estende la classe Server usata per comunicazioni TCP 
class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        # è qui che si svolge tutto l'aspetto di Business Logic (prima fai design di sistema locale, poi quello distribuito dopo)
        self.__user_db = InMemoryUserDatabase() # oggetto normale in Python che funziona da user database (teniamo un riferimento per delegare invocazioni di Client)
        # gli passo lo UserDatabase che è già stato creato
        self.__user_authentication = InMemoryAuthenticationService(self.__user_db) 
    
    # settiamo come gestire eventi per nuove connessioni
    def __on_connection_event(self, event, connection, address, error):
        match event:
            case 'listen':
                print('Server listening on %s:%d' % address) # quando ascolto, avviso client che sto ascoltando
            case 'connect':
                # quando inizio nuova connessione, server attacca callback on_message_event alla connessione
                connection.callback = self.__on_message_event 
            case 'error':
                # quando si verifica errore lo stampiamo e lo ignoriamo
                traceback.print_exception(error)
            case 'stop':
                # una print per lo stop giusto per essere gentili
                print('Server stopped')
    
    def __on_message_event(self, event, payload, connection, error):
        # quando ricevo un evento, verifico che si tratti di un messaggio
        match event:
            case 'message':
                # nel caso sia tutto a posto, deserializzo il messaggio (unmarshalling)
                print('[%s:%d] Open connection' % connection.remote_address)
                request = deserialize(payload)
                # verifico che sia una richiesta, se è così, genero la risposta alla richiesta
                assert isinstance(request, Request)
                print('[%s:%d] Unmarshall request:' % connection.remote_address, request)
                # chiamo qui il metodo handle request che gestisce la richiesta ed elabora la risposta, per poi serializzarla
                # ed inviarla al client
                response = self.__handle_request(request)
                connection.send(serialize(response))
                print('[%s:%d] Marshall response:' % connection.remote_address, response)
                # chiudo poi la connessione che abbiamo presente (solo per scelta è stato fatto)
                # (se vogliamo, possiamo mantenere attiva la connessione, anche se complica abbastanza la cosa e non ha tanti benefici)
                connection.close()
            case 'error':
                # quando si verifica errore stampiamo errore e ignoriamo
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    
    # dentro questo metodo gestiamo la richiesta inviata e generiamo la risposta
    def __handle_request(self, request: Request):
        try:
            # verifico se il servizio richiesto riguarda aggiunte al database oppure se riguarda l'autenticazione
            match request.serviceType:
                case 'databaseService':
                    # altro exploit di Python reflections per trovare una funzione adatta in base al tipo passato
                    method = getattr(self.__user_db, request.name)
                    
                case 'authenticationService':
                    method = getattr(self.__user_authentication, request.name)
                    
                case _:
                    raise Exception("The requested service is not one of those available by the server!")

            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            # catturiamo tutti i possibili errori
            error = " ".join(e.args)
        # tutte le informazioni ottenute (dati di risposta o errori), li mettto dentro la Response
        return Response(result, error)


# è qui che iniziamo il server!
if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
