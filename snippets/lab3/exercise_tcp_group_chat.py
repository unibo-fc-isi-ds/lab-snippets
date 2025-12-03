from multiprocessing.dummy import connection
from datetime import datetime
import threading
import sys
import socket
from unittest import case
import psutil
import time

# ---- CONFIGURAZIONE ----
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

# Ottiene tutti gli indirizzi IP locali della macchina
def local_ips():
    for interface in psutil.net_if_addrs().values(): #itera su tutte le interfacce di rete (wifi, ethernet, ecc.)
        for addr in interface: #esamina ogni indirizzo associato
            if addr.family == socket.AF_INET: #controlla se l'indirizzo è di tipo IPv4
                    yield addr.address #restituisce l'indirizzo IPv4 trovato

# -------- CLASSE PEER --------

class Peer:

    def __init__(self, port):
        # socket SOLO per ascoltare (server)
        self.__listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__listen_socket.bind(address(port=port))

        # lista di connessioni TCP attive (sia in ingresso che in uscita)
        self.__connections: list[socket.socket] = []
        self.__lock = threading.Lock()  # per proteggere __connections

        # callback
        self.__callbackListener = self.on_new_connection
        self.__callbackReceiver = self.on_message_received

        # thread che accetta nuove connessioni
        self.__listener_thread = threading.Thread(
            target=self.__handle_incoming_connections,
            daemon=True
        )
        self.__listener_thread.start()

    # ---- PROPRIETÀ ----

    @property
    def callbackListener(self):
        return self.__callbackListener or (lambda *_: None)

    @callbackListener.setter
    def callbackListener(self, cb):
        self.__callbackListener = cb

    @property
    def callbackReceiver(self):
        return self.__callbackReceiver or (lambda *_: None)

    @callbackReceiver.setter
    def callbackReceiver(self, cb):
        self.__callbackReceiver = cb

    @property
    def closed(self):
        return self.__listen_socket._closed

    @property
    def listPeers(self):
        # restituisce la lista delle connessioni attive (solo info)
        with self.__lock:
            return list(self.__connections)

    # ---- NOTIFICA EVENTI ----

    def on_eventListen(self, event: str, address: tuple = None, error: Exception = None):
        self.callbackListener(event, address, error)

    def on_eventReceive(self, event: str, payload: str = None, error: Exception = None):
        self.callbackReceiver(event, payload, error)

    # ---- CALLBACK DI DEFAULT ----

    def on_new_connection(self, event, address, error):
        match event:
            case 'listen':
                ip, port = address
                print(f"Server listening on port {port} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open connection with peer: {address}")
            case 'stop':
                print("Stop listening for new connections")
            case 'error':
                print(f"Errore accettazione connessioni: {error}")

    def on_message_received(self, event, payload, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                print("Connection with peer closed")
            case 'error':
                print(f"Errore ricezione di messaggi: {error}")

    # ---- THREAD: ASCOLTO CONNESSIONI ----

    def __handle_incoming_connections(self):
        self.__listen_socket.listen()
        self.on_eventListen('listen', self.__listen_socket.getsockname(), None)
        try:
            while True:
                conn, addr = self.__listen_socket.accept()
                with self.__lock:
                    self.__connections.append(conn)
                self.on_eventListen('connect', addr, None)
                # thread dedicato alla ricezione su questa connessione
                t = threading.Thread(
                    target=self.__handle_incoming_messages,
                    args=(conn,),
                    daemon=True
                )
                t.start()
        except OSError as e:
            # socket chiuso localmente
            self.on_eventListen('error', None, e)
        finally:
            self.on_eventListen('stop', None, None)

    # ---- THREAD: RICEZIONE MESSAGGI DA UNA CONNESSIONE ----

    def __handle_incoming_messages(self, conn: socket.socket):
        try:
            while True:
                length_bytes = conn.recv(2)
                if not length_bytes:
                    break
                length = int.from_bytes(length_bytes, 'big')
                if length == 0:
                    break
                data = conn.recv(length)
                if not data:
                    break
                payload = data.decode()
                self.on_eventReceive('message', payload, None)
        except Exception as e:
            self.on_eventReceive('error', None, e)
        finally:
            try:
                conn.close()
            except OSError:
                pass
            with self.__lock:
                if conn in self.__connections:
                    self.__connections.remove(conn)
            self.on_eventReceive('close', None, None)

    # ---- METODI DI INVIO ----

    def send_message(self, msg: str, sender: str):
        if not msg:
            print("Empty message, not sent")
            return
        with self.__lock:
            if not self.__connections:
                print("No peer connected, message is lost")
                return
            text = message(msg.strip(), sender)
            data = text.encode()
            frame = int.to_bytes(len(data), 2, 'big') + data
            dead = []
            for conn in self.__connections:
                try:
                    conn.sendall(frame)
                except OSError:
                    dead.append(conn)
            # rimuovi connessioni morte
            for d in dead:
                try:
                    d.close()
                except OSError:
                    pass
                if d in self.__connections:
                    self.__connections.remove(d)

    # ---- CONNESSIONE A UN ALTRO PEER ----

    def connectPeer(self, peer: str, retries: int = 1, delay: float = 1.0):
        """
        peer: stringa 'ip:port'
        retries: quante volte ritentare in caso di ConnectionRefusedError
        """

        for attempt in range(retries):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(address(*address(peer)))
                with self.__lock:
                    self.__connections.append(s)
                print(f"Connected to peer: {peer}")
                # thread di ricezione per questa connessione
                t = threading.Thread(
                    target=self.__handle_incoming_messages,
                    args=(s,),
                    daemon=True
                )
                t.start()
                return
            except ConnectionRefusedError:
                s.close()
                if attempt < retries - 1:
                    print(f"Peer {peer} non raggiungibile, ritento...")
                    time.sleep(delay)
                else:
                    print(f"Impossibile connettersi a {peer}")
            except OSError as e:
                s.close()
                print(f"Errore connessione a {peer}: {e}")
                break

    # ---- CHIUSURA ----

    def close(self):
        try:
            self.__listen_socket.close()
        except OSError:
            pass
        with self.__lock:
            for conn in self.__connections:
                try:
                    conn.close()
                except OSError:
                    pass
            self.__connections.clear()

######################################################

# ---- MAIN ----
localport = sys.argv[1].strip() #porta su cui ascoltare 
peer = None

if len(sys.argv) > 2:
    peer = sys.argv[2].strip() #ip:porta del peer a cui connettersi

p = Peer(localport) # andrebbe fatto il check che la porta non sia già in uso e che sia un numero valido

#controllo se il peer a cui voglio connettermi è a sua volta connesso ad altri peer

#problema : La lista sarà sempre vuota all'inizio, perché il peer non ha ancora avuto il tempo di connettersi agli altri peer

"""
if not p.listPeers:
    print("No connected peers found.")
else: 
    print("Connected peers:")
    for peer in p.listPeers:
        print(f"- {peer}")  
        p.connectPeer(peer)
"""
if peer is not None:    
    p.connectPeer(peer)

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input() #leggo da stdin il messaggio da inviare
        p.send_message(content, username) #invio il messaggio
    except (EOFError, KeyboardInterrupt): #eccezioni : ctrl+D o ctrl+C
        print("\nExiting chat...")
        p.close()
        break
