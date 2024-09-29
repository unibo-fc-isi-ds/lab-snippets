from snippets.lab2 import *
import sys

max = int(sys.argv[1])
peer = Peer(
    port=0, 
    peers=[address(peer) for peer in sys.argv[2:]]
)

for i in range(max):
    peer.send_all(message(f"Number {i}", sender="Streamer"))
    print(f"Sent message {i}")

peer.close()
