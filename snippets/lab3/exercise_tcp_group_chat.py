from snippets.lab3 import *
import sys

remote_peers: set[Client] = set()

def send_message(msg, sender):
    if not msg:
        print("Empty message, not sent")
        return

    for peer in list(remote_peers):
        peer.send(message(msg.strip(), sender))

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            remote_peers.discard(connection)
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            remote_peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

if len(sys.argv) < 2:
    print("Usage: poetry run python -m snippets -l 3 --exercise <PORT> [<HOST_ENDPOINT1:PORT_ENDPOINT1> <HOST_ENDPOINT2:PORT_ENDPOINT2> ...]")
    sys.exit(1)

try:
    port = int(sys.argv[1])
except ValueError:
    print("Port must be an integer")
    sys.exit(1)

server = Server(port, on_new_connection)
print(port)

for endpoint in sys.argv[2:]:
    peer = Client(address(endpoint), on_message_received)
    remote_peers.add(peer)
    print(f"Connected to {peer.remote_address}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for remote_peer in list(remote_peers):
            remote_peer.close()
        break