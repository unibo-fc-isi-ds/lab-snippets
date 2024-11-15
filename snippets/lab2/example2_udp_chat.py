from snippets.lab2 import *
import threading
import sys


class AsyncPeer(Peer):
    def __init__(self, port, peers=None, callback=None):
        super().__init__(port, peers)
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        self.__callback = callback or (lambda *_: None)
        self.__receiver_thread.start()
    
    def __handle_incoming_messages(self):
        while True:
            message, address = self.receive()
            self.on_message_received(message, address)

    def on_message_received(self, payload, sender):
        self.__callback(payload, sender)


peer = AsyncPeer(
    port = int(sys.argv[1]), 
    peers = [address(peer) for peer in sys.argv[2:]], 
    callback = lambda message, _: print(message)    # A callback is a function stored as data and designed to be called by another function.
                                                    # For instance main calls library function and specifies the callback function that will be called from the library function.
                                                    # This let us define a function without the var message that we do not have at the moment
)

print(f'Bound to: {peer.local_address}')
print(f'Local IP addresses: {list(local_ips())}')
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    content = input()
    peer.send_all(message(content, username))
