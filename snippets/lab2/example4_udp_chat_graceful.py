from snippets.lab2 import *
import threading
import sys


EXIT_MESSAGE = "<LEAVES THE CHAT>"


class AsyncPeer(Peer):
    # uguale a soluzione precedente
    def __init__(self, port, peers=None, callback=None):
        super().__init__(port, peers)
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        self.__callback = callback or (lambda *_: None)
        self.__receiver_thread.start()
    
    def __handle_incoming_messages(self):
        while True:
            message, address = self.receive()
            # in questo caso, rimuoviamo dalla lista di peers collegati quello che sta uscendo
            if message.endswith(EXIT_MESSAGE):
                self.peers.remove(address)
            self.on_message_received(message, address)

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
    try:
        content = input()
        peer.send_all(message(content, username))
    except (EOFError, KeyboardInterrupt): #fondamentale usare catturare solo il tipo necessario che ci interessa di errori (meglio così per capire che errori sto catturando)
        peer.send_all(message(EXIT_MESSAGE, username)) # mandiamo a tutti un messaggio per indicare che stiamo uscendo
        break
peer.close() # quando esce, chiudiamo il socket dell'utente peer
exit(0) # explicit termination of the program with success
