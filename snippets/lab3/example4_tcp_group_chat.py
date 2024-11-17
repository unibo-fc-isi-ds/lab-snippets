from snippets.lab3 import *
import sys

#creo una nuova classe AsyncUser che contiene al suo interno aspetti di Client e Server
class AsyncUser: 
    # durante la sua inizializzazione, conterrà numerosi aspetti della classe server (come uso di Thread per mantenere asincronia)
    # inoltre, al suo interno avrà una variabile interna che avrà una lista di tutti i remote peers a cui lo user sarà collegato
    #(per essere precisi, conterrà tutte le connessioni)
    def __init__(self, port, remote_peers_connections = None,callback=None):
        #se all'inizio non ho alcun indirizzo, non mi devo preoccupare di niente (aspetto che entri altra gente)
        if remote_peers_connections is None:
            remote_peers_connections = set()
        #altrimenti, in questa riga, comincio a stabilire le connessioni (implemento l'aspetto "Client")
        #self.remote_peers = {address(*remote_peer) for peer in remote_peers}
        self.remote_peers_connections = remote_peers_connections
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(address(port=port))
        #qui sto implementando l'aspetto "server" di mettermi in attesa senza bloccarmi
        self.__listener_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True)
        self.__callback = callback
        if self.__callback:
            self.__listener_thread.start()
    
    #decoratore per callback del server (getter e setter)
    @property
    def callback(self):
        return self.__callback or (lambda *_: None)
    
    
    @callback.setter
    def callback(self, value):
        if self.__callback:
            raise ValueError("Callback can only be set once")
        self.__callback = value
        if value:
            self.__listener_thread.start()
    
    #devo trovare un modo per gestire tutte le possibili nuove connessioni (come nel server)
    def __handle_incoming_connections(self):
        self.__socket.listen() #uso il listen per ascoltare
        self.on_event('listen', address=self.__socket.getsockname())
        try:
            #durante il lavoro, aggiungo alla lista di remote peers la nuova connessione creata
            while not self.__socket._closed:
                socket, address = self.__socket.accept()
                connection = Connection(socket)
                self.remote_peers_connections.add(connection)
                self.on_event('connect', connection, address)
        except ConnectionAbortedError as e:
            pass # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')
    
    # con questa nuova funzione implemento la capacità dei "Client" di far cominciare una nuova connessione
    # creo qui il nuovo socket, passandogli la porta e l'indirizzo mio per fare il binding
    # mi serve poi anche una tupla che contiene la port e l'indirizzo di destinazione (quello con cui mi voglio connettere)
    def start_connection(self, port, ip_address, destination):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(address(ip_address, port))
        sock.connect(address(*destination))
        self.remote_peers_connections.add(Connection(sock)) # anche in questo caso aggiungo la connessione del nuovo socket
        #dentro la Connection si crea un Thread nuovo per ricevere
    
    # riutilizzo del metodo on_event del server
    def on_event(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None):
        self.__callback(event, connection, address, error)

    # riutilizzo del metodo close del server
    def close(self):
        self.__socket.close()
        self.__listener_thread.join() #questo i daemon evitano di fare errori a seguito della terminazione del programma

mode = sys.argv[1].lower().strip()
remote_peer: AsyncUser | None = None

#DUE PROBLEMI: 
# - come inizializzare client quando entra
# - gestire casi di fault e inconsistenza dati
#callback per inviare messaggio
def send_message(msg, sender):
    if remote_peer is None:
        print("No peer connected, message is lost")
    elif msg:
        remote_peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

#callback per ricevere messaggio
def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            global remote_peer; remote_peer = None
        case 'error':
            print(error)


if mode == 'starter':
    port = int(sys.argv[2])

    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[1]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = on_message_received
                global remote_peer; remote_peer = connection
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

    server = AsyncUser(port, None ,on_new_connection)
elif mode == 'started':
    remote_endpoint = sys.argv[2]

    remote_peer = AsyncUser(address(remote_endpoint), server, on_message_received)
    print(f"Connected to {remote_peer.remote_address}")


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        if remote_peer:
            remote_peer.close()
        break
if mode == 'starter':
    server.close()