from snippets.lab3 import *
from typing import Set
import sys

EXIT_MESSAGE = "<LEAVES THE CHAT>"

port = int(sys.argv[1])           # Port
peers_endpoint_arg = sys.argv[2:] # Eventual endpoints
peers: Set[Client] = set()        # Known peers

def send_message(msg, sender):
    global peers
    if len(peers) == 0:
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
            global peers
            if connection in peers:
                peers.remove(connection)
                print(f"Connection with peer {connection.remote_address} closed")
        case 'error':
            if isinstance(error, OSError) and error.winerror == 10054: # Windows error code for connection forcibly closed
                pass # Ignore forcibly closed connections
            else:
                print(f"Error occurred: {error}")

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[1]} at [{', '.join(local_ips())}]")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            global peers
            peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(f"Connection error: {error}")

server = Server(port, on_new_connection)

# Connect to all peers
for endpoint in peers_endpoint_arg:
    try:
        peer = Client(address(endpoint), on_message_received)
        peers.add(peer)
        print(f"Connected to {peer.remote_address}")
    except ConnectionRefusedError:
        print(f"Connection to {endpoint} refused")
    except TimeoutError:
        print(f"Connection to {endpoint} timed-out")

# Main execution
try:
    username = input('Enter your username to start the chat:\n')
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    send_message(f"{EXIT_MESSAGE}", username)
finally:
    for peer in peers.copy():  # Avoid concurrent modification, could be done better with a lock
        peer.close()
    server.close()
    sys.stdout.close()
    exit(0)