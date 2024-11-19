from snippets.lab3 import *
import sys

server_peer: Client | None = None

def send_message(msg, sender):
    if server_peer is None:
        print("No peer connected, message is lost")
    elif msg:
        server_peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            global server_peer; server_peer = None
        case 'error':
            print(error)

server_endpoint = sys.argv[1]

server_peer = Client(address(server_endpoint), on_message_received)
print(f"Connected to server: {server_peer.remote_address}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        if server_peer:
            server_peer.close()
        break