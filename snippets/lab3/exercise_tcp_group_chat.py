from multiprocessing.dummy import connection
from snippets.lab2 import *
from snippets.lab3 import *
import threading
import sys

port = sys.argv[1].lower().strip() #porta su cui ascoltare 
peer = sys.argv[2].strip() #ip:porta del peer a cui connettersi
remote_peer: Peer | None = None 

class Peer :

    # ------ COSTRUTTORE ------
    def __init__(self, port, peer=None):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket TCP
        self.__socket.bind(address(port=port)) #bind del socket alla porta specificata in argv[1]
        self.__socket.connect(address(*address(peer))) 
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

    # -- METODO PER GESITIRE L'INVIO DEI MESSAGGI --
    def send_message(msg, sender):
        if remote_peer is None: # nessun peer connesso
            print("No peer connected, message is lost")
        elif msg: #c'è un peer connesso e il messaggio non è vuoto --> posso inviare
            remote_peer.send(message(msg.strip(), sender))
        else: #c'è un peer connesso ma il messaggio è vuoto
            print("Empty message, not sent")

    # ---- METODO DI CHIUSURA ----
    def close(self):
        self.__socket.close()

p = Peer(port, peer) 

#controllo se il peer a cui voglio connettermi è a sua volta connesso ad altri peer
if p.listPeers:
    print("Connected peers:")
    for peer in p.listPeers:
        print(f"- {peer}")  

#provo a connettermi a tutti quei peer
for peer in p.listPeers:
    peer.connect()  

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