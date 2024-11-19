import sys
import threading
from snippets.lab3 import *

# Dictionary to store connected peers
peers = {}

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(f"Message from {connection.remote_address}: {payload}")
            send_to_all(payload, sender_address=connection.remote_address)
        case 'close':
            print(f"Connection with {connection.remote_address} closed")
            peers.pop(connection.remote_address, None)
        case 'error':
            print(f"Error with {connection.remote_address}: {error}")

def send_to_all(message, sender_address=None):
    for addr, conn in peers.items():
        if addr != sender_address:
            try:
                conn.send(message)
            except Exception as e:
                print(f"Failed to send message to {addr}: {e}")
                conn.close()
                peers.pop(addr, None)

def start_server(port):
    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server is listening on port {port} at {', '.join(local_ips())}")
            case 'connect':
                print(f"New connection from {address}")
                connection.callback = on_message_received
                peers[address] = connection
            case 'stop':
                print("Server has stopped listening.")
            case 'error':
                print(f"Server error: {error}")

    server = Server(port, on_new_connection)
    return server

def connect_to_peer(remote_endpoint):
    try:
        client = Client(address(remote_endpoint), on_message_received)
        print(f"Connected to peer at {client.remote_address}")
        peers[client.remote_address] = client
    except Exception as e:
        print(f"Failed to connect to peer {remote_endpoint}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <port> [peer1] [peer2] ...")
        sys.exit(1)

    port = int(sys.argv[1])
    remote_peers = sys.argv[2:]  # List of peer addresses

    # Start the server
    server = start_server(port)

    # Attempt to connect to remote peers
    for peer_addr in remote_peers:
        threading.Thread(target=connect_to_peer, args=(peer_addr,), daemon=True).start()

    username = input("Enter your username to start the chat:\n")
    print("Type your message and press Enter to send. Type 'exit' to quit.")

    try:
        while True:
            user_input = input()
            if user_input.lower() == "exit":
                break
            formatted_message = message(user_input, username)
            send_to_all(formatted_message)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting chat...")
    finally:
        # Close all connections and stop the server
        for conn in peers.values():
            conn.close()
        server.close()
        print("Goodbye!")

if __name__ == "__main__":
    main()
