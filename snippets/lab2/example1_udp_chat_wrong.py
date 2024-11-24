from snippets.lab2 import *
import sys


peer = Peer(
    port = int(sys.argv[1]),
    peers = [address(peer) for peer in sys.argv[2:]]
)

print(f'Bound to: {peer.local_address}')
print(f'Local IP addresses: {list(local_ips())}')
username = input('Enter your username to start the chat:\n')
while True:
    content = input('> ')
    peer.send_all(message(content, username))
    print(peer.receive()[0])
