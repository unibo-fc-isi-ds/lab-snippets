from snippets.lab2 import *
import threading
import sys


class AsyncPeer(Peer):
    def __init__(self, port, peers=None, callback=None):
        super().__init__(port, peers)
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        self.__receiver_thread.start()
        self.__callback = callback or (lambda *_: None)
    
    def __handle_incoming_messages(self):
        while True:
            message, address = self.receive()
            self.on_message_received(message, address)

    def on_message_received(self, payload, sender):
        self.__callback(payload, sender)


port = int(sys.argv[1])
peers = [address(peer) for peer in sys.argv[2:]]
peer = AsyncPeer(port, peers, lambda message, _: print(message))

print(f'Local address: {peer.local_address}')
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    content = input()
    peer.send_all(message(content, username))
