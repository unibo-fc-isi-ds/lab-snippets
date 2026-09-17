from snippets.lab2 import *
import threading
import sys

# Definisco una classe AsyncPeer che estende Peer per gestire la ricezione asincrona dei messaggi 
# --> non blocca l'invio dei messaggi
class AsyncPeer(Peer):
    def __init__(self, port, peers=None, callback=None):
        super().__init__(port, peers)
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True) 
        #crea un thread separato per gestire i messaggi in arrivo in modo asincrono
        #il thread esegue il metodo __handle_incoming_messages
        #daemon=True significa che il thread non impedirà al programma di terminare

        self.__callback = callback or (lambda *_: None) #funzione di callback per gestire i messaggi ricevuti

        self.__receiver_thread.start() #avvia il thread per la ricezione dei messaggi
    
    ## Metodo privato per gestire i messaggi in arrivo
    def __handle_incoming_messages(self):
        while True:
            message, address = self.receive() ## attende e riceve un messaggio (bloccante)
            self.on_message_received(message, address)

    ## Metodo chiamato quando un messaggio viene ricevuto
    def on_message_received(self, payload, sender):
        self.__callback(payload, sender)


peer = AsyncPeer(
    port = int(sys.argv[1]), 
    peers = [address(peer) for peer in sys.argv[2:]], 
    callback = lambda message, _: print(message)
)

print(f'Bound to: {peer.local_address}')
print(f'Local IP addresses: {list(local_ips())}')
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    content = input()
    peer.send_all(message(content, username))

# Risolvo alcuni problemi, ma non tutti
# - E' ancora una comunicazione client-server, non P2P
# - Non c'è terminazione "pulita" del programma (es. invio di un messaggio di uscita ai peer)
# - Non c'è garanzia di autenticità e integrità dei messaggi
# - La connessione non è affidabile (UDP può perdere pacchetti)