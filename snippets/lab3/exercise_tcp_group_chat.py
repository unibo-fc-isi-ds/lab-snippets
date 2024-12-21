
from snippets.lab3 import *
import sys

all_peers = []

def handle_incoming_connection(client_socket):
    while True:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg:
                print(f"Received: {msg}")
                broadcast(msg, client_socket)
            else:
                break
        except ConnectionResetError:
            break
    #Remove peer 
    all_peers.remove(client_socket)
    client_socket.close()

def broadcast(message, sender_socket):
    for peer in all_peers:
        if peer != sender_socket:
            try:
                peer.send(message.encode('utf-8'))
            except Exception:
                continue

def start_server(host, port):
    """Start a TCP server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"New connection from {addr}")
        all_peers.append(client_socket)
        threading.Thread(target=handle_incoming_connection, args=(client_socket,)).start()

def connect_to_peer(host, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        all_peers.append(client_socket)
        threading.Thread(target=handle_incoming_connection, args=(client_socket,)).start()
    except Exception as e:
        print(f"Could not connect to {host}:{port} - {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: poetry run python exercise_tcp_group_chat.py <host> <port> [peer_host:peer_port ...]")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    peers = sys.argv[3:]

    # Start the server
    threading.Thread(target=start_server, args=(host, port)).start()

    # Connect to specified peers
    for peer in peers:
        peer_host, peer_port = peer.split(":")
        connect_to_peer(peer_host, int(peer_port))

    # Input loop to send messages
    while True:
        msg = input("Enter message: ")
        broadcast(msg, None)
