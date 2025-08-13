import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from snippets.lab3 import *

# List to keep track of connected clients
connected_clients = []

# Function to broadcast messages to all clients except the sender
def broadcast_message(message, sender_connection):
    for client in connected_clients:
        if client != sender_connection:
            try:
                client.send(message)
            except Exception as e:
                print(f"Error sending message to {client.remote_address}: {e}")
                client.close()

# Callback function to handle incoming messages on server
def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(f"Message from {connection.remote_address}: {payload}")
            broadcast_message(payload, connection)  # Broadcast the message to all clients
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            connected_clients.remove(connection)  # Remove client on disconnect
        case 'error':
            print(f"Error: {error}")

# Callback for new connections on server
def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on {address[0]}:{address[1]}")
        case 'connect':
            print(f"New connection from {address}")
            connection.callback = on_message_received
            connected_clients.append(connection)  # Add client to list
        case 'stop':
            print("Server stopped listening.")
        case 'error':
            print(f"Error: {error}")

# Server Setup
def run_server(port):
    server = Server(port, on_new_connection)
    print(f"Server started. Waiting for clients to connect on port {port}...")
    try:
        while True:
            pass  # Keep server running
    except KeyboardInterrupt:
        print("Server is shutting down.")
    finally:
        server.close()

# Client message send function
def send_message(message, connection):
    if message:
        connection.send(message)
    else:
        print("Empty message, not sent")

# Callback function to handle incoming messages on client
def on_client_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(f"Message from server: {payload}")
        case 'close':
            print("Disconnected from server.")
        case 'error':
            print(f"Error: {error}")

# Client Setup
def run_client(remote_host, remote_port):
    remote_peer = Client((remote_host, remote_port), on_client_message_received)
    print(f"Connected to server at {remote_peer.remote_address}")

    # Start client chat loop
    try:
        while True:
            message = input("Enter your message: ")
            send_message(message, remote_peer)
    except (EOFError, KeyboardInterrupt):
        print("Shutting down client.")
    finally:
        remote_peer.close()

# Main execution logic
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python exercise_tcp_group_chat.py <server|client> [host] [port]")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == 'server':
        # Start server mode
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 1234
        run_server(port)
    elif mode == 'client':
        # Start client mode
        if len(sys.argv) < 4:
            print("Usage for client: python exercise_tcp_group_chat.py client <host> <port>")
            sys.exit(1)
        remote_host = sys.argv[2]
        remote_port = int(sys.argv[3])
        run_client(remote_host, remote_port)
    else:
        print("Unknown mode. Use 'server' or 'client'.")
