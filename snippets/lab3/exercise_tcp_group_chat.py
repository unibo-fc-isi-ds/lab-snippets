from snippets.lab3 import *
import sys
from typing import Optional


peers: set[Client] = set()

def broadcast_message(msg: str, sender: str) -> None:
    if not peers:
        print("No peers connected, message not sent")
    elif msg.strip():
        for peer in peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def handle_received_message(event: str, payload: str, connection: Connection, error: Optional[str]) -> None:
    if event == 'message':
        print(f"Message received: {payload}")
    elif event == 'close':
        print(f"Connection with {connection.remote_address} closed")
        peers.discard(connection)
    elif event == 'error' and error:
        print(f"Error: {error}")

def handle_new_connection(event: str, connection: Connection, address: tuple, error: Optional[str]) -> None:
    if event == 'listen':
        print(f"Server is now listening on port {address[0]} at {', '.join(local_ips())}")
    elif event == 'connect':
        print(f"New incoming connection from: {address}")
        connection.callback = handle_received_message
        peers.add(connection)
    elif event == 'stop':
        print("Stopped listening for new connections")
    elif event == 'error' and error:
        print(f"Connection error: {error}")

# Input: server port and list of known peer ports
port = int(sys.argv[1])
server = Server(port, handle_new_connection)

# Attempt to connect to each known peer
for peer_port in sys.argv[2:]:
    try:
        peer = Client(address(peer_port), handle_received_message)
        peers.add(peer)
        print(f"Successfully connected to {peer.remote_address}")
    except Exception as e:
        print(f"Error connecting to {peer_port}: {e}")

# Prompt for username to start the chat
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send. Messages from other peers will appear below.')

# Chat loop
try:
    while True:
        content = input()
        broadcast_message(content, username)
except (EOFError, KeyboardInterrupt):
    print("Closing chat...")
    for peer in list(peers):
        peer.close()
    server.close()
    print("Chat closed.")

