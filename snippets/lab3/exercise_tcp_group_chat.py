from snippets.lab3 import *
import sys

peers: set[Client] = set()

def send_message(msg, sender):
    if peers is None:
        print("No peer connected, message is lost")
    elif msg:
        for peer in peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if connection in peers:
                peers.remove(connection)
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

# Input: current port + list of the other existing peer ports
port = int(sys.argv[1])
server = Server(port, on_new_connection)

# Connect to known peers
for peer_port in sys.argv[2:]:
    try:
        peer = Client(address(peer_port), on_message_received)
        peers.add(peer)
        print(f"Connected to {peer.remote_address}")
    except Exception as e:
        print(f"Failed to connect to {peer_port}: {e}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

# Chat loop
try:
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    for peer in list(peers):
        peer.close()

    server.close()
    print("Chat closed.")
