from snippets.lab3 import *
import sys

#creo una nuova classe AsyncUser che contiene al suo interno aspetti di Client e Server
class AsyncUser:
    # durante la sua inizializzazione, conterrà numerosi aspetti della classe server (come uso di Thread per mantenere asincronia)
    # inoltre, al suo interno avrà una variabile interna che avrà una lista di tutti i remote peers a cui lo user sarà collegato
    #(per essere precisi, conterrà tutte le connessioni)
    def __init__(self, port, username, remote_peers_connections=None, callback=None):
        #se all'inizio non ho alcun indirizzo, non mi devo preoccupare di niente (aspetto che entri altra gente)
        if remote_peers_connections is None:
            remote_peers_connections = set()
        self.username = username # qui setto lo username
        # altrimenti, in questa riga, comincio a stabilire le connessioni (implemento l'aspetto "Client")
        #self.remote_peers = {address(*remote_peer) for peer in remote_peers}
        self.remote_peers_connections = remote_peers_connections
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(address(port=port))
        #qui sto implementando l'aspetto "server" di mettermi in attesa senza bloccarmi
        self.__listener_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True)
        self.__callback = callback
        self.__active = True # per verificare se questo sia ancora attivo e partecipe alla connessione
        if self.__callback:
            self.__listener_thread.start()
        # semplici messaggi per dire che sono entrato con una certa porta
        print(f"Chat user started on port {port}")
        print(f"Your local IPs: {', '.join(local_ips())}")

    # decoratore per callback del server (getter e setter)
    @property
    def callback(self):
        return self.__callback or (lambda *_: None)
    
    # decoratore per settare callback
    @callback.setter
    def callback(self, value):
        if self.__callback:
            raise ValueError("Callback can only be set once")
        self.__callback = value
        if value:
            self.__listener_thread.start()

    # un metodo per gestire tutte le possibili nuove connessioni (come nel server)
    def __handle_incoming_connections(self):
        self.__socket.listen() # rimane in attesa di nuove connessioni
        self.on_event('listen', address=self.__socket.getsockname())
        try:
            # quando svolgo tale compito, se verifico che non è chiuso e che è ancora attivo, accetto nuovi utenti, genero nuove connessioni
            # e le aggiungo alla lista di peers connessi
            while self.__active and not self.__socket._closed:
                socket, address = self.__socket.accept()
                connection = Connection(socket, self.__handle_peer_message)
                if not self.__is_duplicate_connection(connection):
                    self.remote_peers_connections.add(connection)
                    self.on_event('connect', connection, address)
                    # Notifico qui tutti i peers che è entrato un nuovo utente
                    self.broadcast_message(message(f"has joined the chat!", self.username))
        except ConnectionAbortedError:
            pass # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            # come sicurezza fermo l'evento se la cosa non è stata gestita da close
            if self.__active:
                self.on_event('stop')
    
    def __is_duplicate_connection(self, new_connection):
        for conn in self.remote_peers_connections:
            if (conn.remote_address == new_connection.remote_address and 
                not conn.closed):
                return True
        return False

    # con questa nuova funzione implemento la capacità dei "Client" di far cominciare una nuova connessione
    # creo qui il nuovo socket, passandogli la porta e l'indirizzo mio per fare il binding
    # mi serve poi anche una tupla che contiene la port e l'indirizzo di destinazione (quello con cui mi voglio connettere)
    def start_connection(self, port, ip_address, destination):
        try:
            for conn in self.remote_peers_connections:
                if conn.remote_address == (destination[0], destination[1]) and not conn.closed:
                    print(f"Already connected to {destination[0]}:{destination[1]}")
                    return None
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # problema qui inusuale: quando introduco il terzo utente e faccio la socket bind
            # nonostante gli passo indirizzo 0.0.0.0 (come tutti gli altri) e una porta diversa da loro
            # mi va in errore dicendo (di norma è consentito un solo utilizzo di ogni singolo indirizzo di socket)
            sock.bind(address(ip_address, port)) 
            sock.connect(address(*destination))
            # anche in questo caso aggiungo la connessione del nuovo socket
            # dentro la Connection si crea un Thread nuovo per ricevere
            connection = Connection(sock, self.__handle_peer_message)
            self.remote_peers_connections.add(connection)
            # invio qui un messaggio per dire che si è unito qualcuno
            connection.send(message(f"has connected from {ip_address}:{port}!", self.username))
            return connection
        except ConnectionAbortedError as e:
            pass # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')

    # un metodo per gestire i messaggi dei peers
    def __handle_peer_message(self, event: str, payload: str, connection: Connection, error: Exception):
        # verifico prima di tutto se effettivamente si tratta di un nuovo messaggio e in tal caso lo invia a tutti i peers
        if event == 'message':
            self.broadcast_message(payload, exclude=connection)
            self.on_event('message', connection, payload=payload)
        elif event == 'error':
            print(f"Connection error: {error}")
            self.remove_peer(connection)
        elif event == 'close':
            self.remove_peer(connection)
            self.broadcast_message(message("has left the chat!", self.username))

    # questo è il metodo che invia a tutti i peer connessi il messaggio inviato a tutti gli altri peer
    def broadcast_message(self, msg, exclude=None):
        # controlla se la connessione è ancora aperta (e che non stia per inviarsi un messaggio da solo a se stesso)
        dead_connections = set()
        active_connections = set(conn for conn in self.remote_peers_connections if not conn.closed)
        for conn in active_connections:
            if conn != exclude:
                try:
                    conn.send(msg)
                except Exception as e:
                    print(f"Failed to send to peer: {e}")
                    dead_connections.add(conn)
        
        # se ci sono delle connessioni "morte" (che ora non esistono più), le rimuove
        for conn in dead_connections:
            self.remove_peer(conn)

    # questa è la funzione dove si sfrutta message (che trasforma string in bytes) e invia messaggi
    def send_message(self, text):
        if self.__active:
            msg = message(text, self.username)
            self.broadcast_message(msg)

    # quando un peer esce, si richiama questa funzione per andare a chiudere la connessione e a rimuoverlo dalla lista di peer connessi
    def remove_peer(self, connection):
        if connection in self.remote_peers_connections:
            self.remote_peers_connections.remove(connection)
            if not connection.closed:
                connection.close()

    # metodo per gestire callbacks in base a determinati eventi (passo il "tipo" di evento, poi la connessione, l'indirizzo, possibile errore e payload)
    def on_event(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None, payload: str=None):
        self.__callback and self.__callback(event, connection, address, error, payload)

    # questo importantissimo metodo mi serve per chiudere le connessioni
    def close(self):
        # prima di tutto verifico che sia ancora attivo e funzionante
        if self.__active:
            self.__active = False
            # si fa prima notifica che si sta uscendo
            self.broadcast_message(message("is disconnecting!", self.username))
            
            # poi si chiude il suo socket
            self.__socket.close()
            
            # aspetto che il thread finisca di fare il suo lavoro e poi continuo
            if self.__listener_thread.is_alive():
                self.__listener_thread.join()
            
            print(f"User {self.username} has left the chat.")

# una funzione che utilizziamo per far cominciare la chat a partire da console
def run_chat_user(port, username, initial_peers=None):
    # al suo interno contiene una prima callback chiamata "handle_events" per gestire i possibili eventi (invio messaggio, nuova connessione, in ascolto...)
    def handle_events(event, connection, address, error, payload):
        if event == 'message':
            print(payload)
        elif event == 'connect':
            print(f"New connection from {address}")
        elif event == 'error':
            print(f"Error: {error}")
        elif event == 'listen':
            print(f"Listening on {address}")
        elif event == 'stop':
            print("Stopped listening")

    # creo poi un nuovo utente e in base al numero di peers passati all'inizio, mi connetto con tutti quelli passati
    user = AsyncUser(port, username, callback=handle_events)
    
    if initial_peers:
        for peer_ip, peer_port in initial_peers:
            try:
                connection = user.start_connection(0, "0.0.0.0", destination=(peer_ip, peer_port))
                if connection:
                    print(f"Successfully connected to {peer_ip}:{peer_port}")
            except Exception as e:
                print(f"Failed to connect to {peer_ip}:{peer_port}: {e}")

    # metodo per gestire testo input passato, se scrivo "/quit" (o se ci sono errori EOF o scrivo ^C), questo esce, sennò invia il messaggio
    def input_handler():
        while True:
            try:
                text = input()
                if text.lower() == '/quit':
                    break
                else:
                    user.send_message(text)
            except (EOFError, KeyboardInterrupt):
                break
        user.close()

    input_thread = threading.Thread(target=input_handler)
    input_thread.start()
    return user


# per cominciare ad usarlo
if __name__ == "__main__":
    
    # verifico che quando scrivo a linea di comando inserisco sempre 
    if len(sys.argv) < 3:
        print("Usage: poetry run python -m snippets -l 3 -e 4 <port> <username> [peer_ip:peer_port ...]")
        sys.exit(1)

    port = int(sys.argv[1])
    username = sys.argv[2]
    initial_peers = [address(peer) for peer in sys.argv[3:]]
    
    user = run_chat_user(port, username, initial_peers)