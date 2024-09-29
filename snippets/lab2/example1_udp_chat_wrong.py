from snippets.lab2 import *
import sys


port = int(sys.argv[1])
peers = [address(peer) for peer in sys.argv[2:]]
peer = Peer(port, peers)

print(f'Local address: {peer.local_address}')
username = input('Enter your username to start the chat:\n')
while True:
    content = input('> ')
    peer.send_all(message(content, username))
    print(peer.receive()[0])
