from snippets.lab3 import *
import sys

mode = sys.argv[1].lower().strip()
remote_peers = []  # List of connected peers (server side only)


def send_message(msg, sender):
    """Sends a message to all connected peers."""
    if not remote_peers:
        print("No peers connected, message lost")
    elif msg.strip():
        for peer in remote_peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    """Handles received messages and other events."""
    match event:
        case 'message':
            print(payload)  
            if mode == 'server':
                for peer in remote_peers:
                    if peer != connection:  
                        peer.send(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if mode == 'server' and connection in remote_peers:
                remote_peers.remove(connection)
        case 'error':
            print(f"Error: {error}")


if mode == 'server':
    port = int(sys.argv[2])

    def on_new_connection(event, connection, address, error):
        """Handles new incoming connections."""
        match event:
            case 'listen':
                print(f"Server listening on port {port} at address {', '.join(local_ips())}")
            case 'connect':
                print(f"New connection from: {address}")
                connection.callback = on_message_received
                remote_peers.append(connection) 
            case 'stop':
                print("Stopped listening for new connections")
            case 'error':
                print(f"Error: {error}")

    server = Server(port, on_new_connection)

elif mode == 'client':
    remote_endpoint = sys.argv[2]
    remote_peer = Client(address(remote_endpoint), on_message_received)
    remote_peers.append(remote_peer)  
    print(f"Connected to server {remote_peer.remote_address}")


username = input("Insert your username to start chatting:\n")
print("Write your message here and press enter. Other people's messages will be displayed here.")

try:
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    print("Disconnecting...")
    for peer in remote_peers:
        peer.close()  
    if mode == 'server':
        server.close()
