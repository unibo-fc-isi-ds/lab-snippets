from snippets.lab2 import *
import threading
import sys


# Creiamo qui una nuova soluzione tramite l'utilizzo di Thread. Questa nuova classe è una variante del Peer che riceve i messaggi
# in maniera asincrona
class AsyncPeer(Peer):
    def __init__(self, port, peers=None, callback=None):
        super().__init__(port, peers)
        # qui sotto utilizzo un thread che gestisce tutto l'aspetto di ricevere un messaggio
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        self.__callback = callback or (lambda *_: None)
        self.__receiver_thread.start()
    
    # funzione passata a Thread per gestire messaggi in arrivo
    def __handle_incoming_messages(self):
        while True:
            message, address = self.receive() # recupera messaggio e indirizzo usando la funzione di Peer
            self.on_message_received(message, address) #poi passa questi dati alla funzione on_message_received

    def on_message_received(self, payload, sender):
        self.__callback(payload, sender) 
        # richiamo qui la callback (ovvero la funzione di stampa messaggio, passando payload ovvero il messaggio e ip + port messaggero


peer = AsyncPeer(
    port = int(sys.argv[1]), 
    peers = [address(peer) for peer in sys.argv[2:]], 
    callback = lambda message, _: print(message) # è su callback che abbiamo fatto collassare il lavoro di ricezione messaggi
    # utilizzo una funzione lambda che prende in ingresso messaggio e lo stampa
    # la callback è essenzialmente una funzione riferimento che viene creata per fare sì che quando la libreria venga fatta 
    # deve fare una chiamata a tale funzione (di cui non si sa quando avverrà), questa saprà cosa deve svolgere in quei momenti
    # in questo caso, libreria saprà come deve comportarsi nell'istante in cui riceve un messaggio
    # fondamentale il modo in cui è scritto perchè se non specifico message, non sa che il tutto si deve svolgere in quei casi
)

print(f'Bound to: {peer.local_address}')
print(f'Local IP addresses: {list(local_ips())}')
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    content = input()
    peer.send_all(message(content, username))
    # notare che qui non riceviamo più i messaggi in maniera esplicita!
