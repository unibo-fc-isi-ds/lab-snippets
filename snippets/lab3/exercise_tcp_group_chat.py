from snippets.lab3 import *
import socket
import threading
import sys

BUFFER_SIZE = 1024
EXIT_MESSAGE = "<LEAVES THE CHAT>"

# Store known peers in a set to broadcast messages
known_peers = set()

def broadcast_message(msg, sender):
    """Send the message to all known peers."""
    for peer in list(known_peers):
        try:
            peer.send(message(msg.strip(), sender))
        except Exception as e:
            print(f"Failed to send to {peer.remote_address}: {e}")
            known_peers.remove(peer)

def on_message_received(event, payload, connection, error):
    """Callback for handling incoming messages."""
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if connection in known_peers:
                known_peers.remove(connection)
        case 'error':
            print(error)

def handle_new_connection(event, connection, address, error):
    """Callback for handling new incoming connections on the server side."""
    match event:
        case 'listen':
            print(f"Server listening at {address[0]} on local IPs: {', '.join(local_ips())}")
        case 'connect':
            print(f"Connected to new peer at {address}")
            connection.callback = on_message_received
            known_peers.add(connection)  # Track this peer for broadcasting
        case 'error':
            print(error)
        case 'stop':
            print("Server stopped listening for new connections")

# Start as both server and client in a peer-to-peer setup
port = int(sys.argv[1])
server = Server(port, handle_new_connection)

# Connect to initially known peers based on command-line arguments
for peer_endpoint in sys.argv[2:]:
    try:
        client_peer = Client(address(peer_endpoint), on_message_received)
        known_peers.add(client_peer)
        print(f"Connected to {client_peer.remote_address}")
    except Exception as e:
        print(f"Failed to connect to {peer_endpoint}: {e}")

# Enter chat loop
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

try:
    while True:
        content = input()
        if content.lower() == "/exit":
            broadcast_message(EXIT_MESSAGE, username)
            break
        broadcast_message(content, username)
except (EOFError, KeyboardInterrupt):
    broadcast_message(EXIT_MESSAGE, username)
finally:
    for peer in list(known_peers):
        peer.close()
    server.close()
    print("Chat closed.") 
