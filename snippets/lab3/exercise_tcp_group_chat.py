from snippets.lab3 import *
import sys


peers: list[Connection] = []
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <my_port> [peer_address1 peer_address2 ...]")
    sys.exit(1)

my_port = int(sys.argv[1])
known_peers = sys.argv[2:]


def send_message(msg, sender):
    if not msg:
        print("Empty message, not sent")
        return

    network_message = message(msg.strip(), sender)
    
    if not peers:
        print("No peers connected, listening for connections...")
    else:
        for peer in peers:
            try:
                peer.send(network_message)
            except Exception as e:
                print(f"Failed to send to {peer.remote_address}: {e}")


def on_peer_event(event, payload, connection, error):
    match event:
        case 'message':
            print(f"\n[{connection.remote_address}] {payload}")
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if connection in peers:
                peers.remove(connection)
        case 'error':
            print(f"Error with peer {connection.remote_address}: {error}")

def on_incoming_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Peer listening on port {my_port}")
        case 'connect':
            print(f"Accepted connection from: {address}")
            connection.callback = on_peer_event
            peers.append(connection)
        case 'error':
            print(f"Server error: {error}")

server = Server(my_port, on_incoming_connection)
for peer_addr in known_peers:
    try:
        print(f"Connecting to {peer_addr}...")
        new_client = Client(address(peer_addr), on_peer_event)
        peers.append(new_client)
        print(f"Connected to {new_client.remote_address}")
    except Exception as e:
        print(f"Could not connect to {peer_addr}: {e}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt): # Ctrl+D or Ctrl+C to exit
        print("\nClosing chat...")
        break

if 'server' in locals():
    server.close()

for peer in peers:
    peer.close()
