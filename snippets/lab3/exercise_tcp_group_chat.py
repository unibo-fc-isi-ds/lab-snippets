from multiprocessing.dummy import connection
from datetime import datetime
import threading
import sys
import socket

localport = sys.argv[1].strip() #porta su cui ascoltare 
peer = None

# Fa il parsing di un indirizzo IP e porta 
def address(ip='0.0.0.0:0', port=None):
    ip = ip.strip()
    if ':' in ip:
        ip, p = ip.split(':')
        p = int(p)
        port = port or p
    if port is None:
        port = 0
    if not isinstance(port, int):
        port = int(port)
    assert port in range(0, 65536), "Port number must be in the range 0-65535"
    assert isinstance(ip, str), "IP address must be a string"
    return ip, port

# Crea un messaggio formattato con timestamp, mittente e testo
def message(text: str, sender: str, timestamp: datetime=None):
    if timestamp is None:
        timestamp = datetime.now()
    return f"[{timestamp.isoformat()}] {sender}:\n\t{text}"

# Classe Peer per la comunicazione TCP tra peer
class Peer :

    # ------ COSTRUTTORE ------
    def __init__(self, port, peer=None):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket TCP
        self.__socket.bind(address(port=port)) #bind del socket alla porta specificata in argv[1]

        if peer is not None:
            self.connectPeer(peer) #provo a connettermi al peer remoto
        
        self.__listPeers = [] #lista dei peer connessi

        self.__listener_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True) #thread per gestire le connessioni in ingresso
        self.__callbackListener = self.on_message_received
        self.__listener_thread.start()
        
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True) #thread per gestire la ricezione dei messaggi
        self.__callbackReceiver = self.on_new_connection
        self.__receiver_thread.start()

    # ---- GETTER ----
    @property #getter per la callback ascolto connessioni
    def callbackListener(self):
        return self.__callbackListener or (lambda *_: None)
    
    @property #getter per la callback ricezione messaggi
    def callbackReceiver(self):
        return self.__callbackReceiver or (lambda *_: None)
    
    @property #getter per lo stato della connessione
    def closed(self):
        return self.__socket._closed

    @property #getter per la lista dei peer connessi
    def listPeers(self):
        return self.__listPeers
    
    # ---- METODO THREAD ASCOLTO CONNESSIONI----
    #serve al thread per gestire le connessioni in ingresso e notifica gli eventi alla callback
    def __handle_incoming_connections(self):
        self.__socket.listen() #mette il socket in ascolto per connessioni in ingresso
        self.on_eventListen('listen', address=self.__socket.getsockname())
        try:
            while not self.__socket._closed: #finché il socket non è chiuso
                socket, address = self.__socket.accept() #accetta una connessione in ingresso
                self.on_eventListen('connect', address) 
        except ConnectionAbortedError as e:
            pass # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_eventListen('error', error=e)
        finally:
            self.on_eventListen('stop')

    # ---- METODO THREAD RICEZIONE MESSAGGI ----
    #serve al thread per gestire i messaggi in ingresso e notifica gli eventi alla callback
    def __handle_incoming_messages(self):
        try:
            while not self.closed: # finché la connessione non è chiusa
                message = self.receive() #BLOCCANTE --> attende la ricezione di un messaggio
                if message is None:
                    break
                self.on_eventReceive('message', message)
        except Exception as e:
            if self.closed and isinstance(e, OSError): 
                return # silently ignore error, because this is simply the socket being closed locally
            self.on_eventReceive('error', error=e)
        finally:
            self.close()

    # ---METODO PER NOTIFICARE LA CALLBACK ---
    #metodo per notificare gli eventi alla callback
    def on_eventListen(self, event: str, address: tuple=None, error: Exception=None):
        self.__callbackListener(event, address, error)

    def on_eventReceive(self, event: str, payload: str=None, error: Exception=None):
        self.__callbackReceiver(event, payload, error)

    # --- CALLBACK : ----

    #gestione delle nuove connessioni in arrivo
    def on_new_connection(event, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                global remote_peer #cambio il valore della variabile globale
                remote_peer = Peer
                self.__listPeers.append(Peer(address)) #aggiungo il peer alla lista dei peer connessi
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

    #gestione dei messaggi ricevuti
    def on_message_received(event, payload, error):
        match event:
            case 'message': 
                print(payload)
            case 'close':
                print(f"Connection with peer closed")
                global remote_peer #cambio il valore della variabile globale
                remote_peer = None #non c'è più nessun peer connesso
            case 'error':
                print(error)

    # ---- METODO DI INVIO MESSAGGI ----
    def send_message(self, msg, sender):
        if remote_peer is None: # nessun peer connesso
            print("No peer connected, message is lost")
        elif msg: #c'è un peer connesso e il messaggio non è vuoto --> posso inviare
            remote_peer.send(message(msg.strip(), sender))
        else: #c'è un peer connesso ma il messaggio è vuoto
            print("Empty message, not sent")

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
    
    ## -- METODO PER CONNETERSI A UN PEER
    def connectPeer(self, peer):
        try:
            self.__socket.connect(address(*address(peer))) #mi connetto al peer
            print(f"Connected to peer: {peer}")
            self.__listPeers.append(peer) # lo aggiungo alla lista dei peer
        except Exception as e :
            pass

    # ---- METODO DI CHIUSURA ----
    def close(self):
        self.__socket.close()

######################################################
remote_peer: Peer | None = None 


if len(sys.argv) > 2:
    peer = sys.argv[2].strip() #ip:porta del peer a cui connettersi

p = Peer(localport, peer) 

#controllo se il peer a cui voglio connettermi è a sua volta connesso ad altri peer
if not p.listPeers:
    print("No connected peers found.")
else: 
    print("Connected peers:")
    for peer in p.listPeers:
        print(f"- {peer}")  
        p.connectPeer(peer)

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input() #leggo da stdin il messaggio da inviare
        p.send_message(content, username) #invio il messaggio
    except (EOFError, KeyboardInterrupt): #eccezioni : ctrl+D o ctrl+C
        if remote_peer: #se c'è un peer connesso
            remote_peer.close() #chiudo la connessione
        break 