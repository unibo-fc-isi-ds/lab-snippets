from snippets.lab2 import *
import threading

#Questa classe contiene una serie di utiliy functions per la gestione di connessioni TCP

## Classe Connection: rappresenta una connessione TCP tra due peer
class Connection:
    def __init__(self, socket: socket.socket, callback=None):
        self.__socket = socket
        self.local_address = self.__socket.getsockname() ## indirizzo locale della connessione
        self.remote_address = self.__socket.getpeername() ## indirizzo remoto della connessione
        self.__notify_closed = False #flag per notificare la chiusura della connessione 
        self.__callback = callback 
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        if self.__callback: #se viene fornita una callback, avvia il thread di ricezione
            self.__receiver_thread.start()

    #getter per la callback
    @property 
    def callback(self):
        return self.__callback or (lambda *_: None)
    
    #setter per la callback
    @callback.setter 
    def callback(self, value):
        if self.__callback: #se la callback è già stata impostata, solleva un'eccezione
            raise ValueError("Callback can only be set once")
        
        self.__callback = value #imposta la nuova callback
        
        if value: #se la callback è valida, avvia il thread di ricezione
            self.__receiver_thread.start()

    @property #getter per lo stato della connessione
    def closed(self):
        return self.__socket._closed
    
    # invia un messaggio attraverso la connessione
    def send(self, message):
        if not isinstance(message, bytes): #se il messaggio non è in bytes, lo converto
            message = message.encode()
            message = int.to_bytes(len(message), 2, 'big') + message
        self.__socket.sendall(message) # invia tutti i byte finché non sono stati inviati
        #__socket.send invece restituisce il numero di byte effettivamente inviati, quindi potrebbe essere necessario richiamarlo più volte 

    # riceve un messaggio dalla connessione
    def receive(self):
        length = int.from_bytes(self.__socket.recv(2), 'big') #carica la lunghezza del messaggio
        if length == 0:
            return None
        return self.__socket.recv(length).decode() # riceve il messaggio e lo decodifica
    
    # chiude la connessione
    def close(self):
        self.__socket.close()
        if not self.__notify_closed: #se non è già stata notificata la chiusura
            self.on_event('close') #notifico la chiusura della connessione (evento 'close')
            self.__notify_closed = True 

    # gestisce i messaggi in arrivo in un thread separato
    def __handle_incoming_messages(self):
        try:
            while not self.closed: # finché la connessione non è chiusa
                message = self.receive() #BLOCCANTE --> attende la ricezione di un messaggio
                if message is None:
                    break
                self.on_event('message', message)
        except Exception as e:
            if self.closed and isinstance(e, OSError): 
                return # silently ignore error, because this is simply the socket being closed locally
            self.on_event('error', error=e)
        finally:
            self.close()

    # metodo generico per notificare gli eventi alla callback
    def on_event(self, event: str, payload: str=None, connection: 'Connection'=None, error: Exception=None):
        if connection is None: #se non è stata fornita una connessione, uso self
            connection = self
        self.callback(event, payload, connection, error)

## Classe Client: è UNA connessione TCP verso un server
#Eredita tutta la logica da Connection
class Client(Connection):
    def __init__(self, server_address, callback=None): #costruisce la connessione nel costruttore
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(address(port=0)) #associa il socket a una porta libera (bloccante)
        sock.connect(address(*server_address)) #stabilisce la connessione al server (bloccante)
        super().__init__(sock, callback) 

## Classe Server: rappresenta tante connessioni TCP in ingresso
class Server:
    def __init__(self, port, callback=None):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(address(port=port)) #bind del socket alla porta specificata
        self.__listener_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True)
        self.__callback = callback
        if self.__callback: #se viene fornita una callback, avvia il thread di ascolto
            self.__listener_thread.start()

    @property #getter per la callback
    def callback(self):
        return self.__callback or (lambda *_: None)
    
    @callback.setter #setter per la callback
    def callback(self, value):
        if self.__callback:
            raise ValueError("Callback can only be set once")
        self.__callback = value
        if value:
            self.__listener_thread.start()
    
    #serve al thread per gestire le connessioni in ingresso e notifica gli eventi alla callback
    def __handle_incoming_connections(self):
        self.__socket.listen() #mette il socket in ascolto per connessioni in ingresso
        self.on_event('listen', address=self.__socket.getsockname())
        try:
            while not self.__socket._closed: #finché il socket non è chiuso
                socket, address = self.__socket.accept() #BLOCCANTE : accetta una connessione in ingresso
                connection = Connection(socket) #crea una connessione per il socket accettato
                self.on_event('connect', connection, address) 
        except ConnectionAbortedError as e:
            pass # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')

    #metodo per notificare gli eventi alla callback
    def on_event(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None):
        self.__callback(event, connection, address, error)

    def close(self):
        self.__socket.close()
