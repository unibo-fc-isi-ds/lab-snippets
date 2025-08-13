import socket
import threading
import sys

# Dizionario per tracciare i client connessi (solo lato server)
clients = {}
lock = threading.Lock()  # Lock per proteggere l'accesso concorrente al dizionario

def broadcast_message(message, sender):
    """
    Invia un messaggio a tutti i client connessi.
    """
    with lock:
        for username, conn in clients.items():
            if username != sender:  # Non rispedire al mittente
                try:
                    conn.sendall(f"[{sender}] {message}\n".encode())
                except Exception as e:
                    print(f"Error broadcasting to {username}: {e}")

def handle_client(conn, addr):
    """
    Gestisce la comunicazione con un singolo client.
    """
    print(f"New connection from {addr}")
    try:
        conn.sendall("Welcome! Please enter your username:\n".encode())
        username = conn.recv(1024).decode().strip()
        if not username:
            conn.close()
            return

        with lock:
            clients[username] = conn
        print(f"User '{username}' connected. Active clients: {list(clients.keys())}")
        broadcast_message(f"{username} has joined the chat!", "Server")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode().strip()
            print(f"[{username}] {message}")
            broadcast_message(message, username)
    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        with lock:
            if username in clients:
                del clients[username]
        broadcast_message(f"{username} has left the chat.", "Server")
        conn.close()

def start_server(host, port):
    """
    Avvia il server di chat.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server started on {host}:{port}")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("Shutting down server.")
    finally:
        server_socket.close()

def start_client(host, port):
    """
    Avvia un client di chat.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f"Connected to chat server at {host}:{port}")

    def receive_messages():
        """
        Thread per ricevere messaggi dal server.
        """
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    print("Disconnected from server.")
                    break
                print(data.decode().strip())
            except Exception as e:
                print(f"Error receiving messages: {e}")
                break

    def send_messages():
        """
        Invio di messaggi al server.
        """
        username = input("Enter your username: ").strip()
        client_socket.sendall(f"{username}\n".encode())
        try:
            while True:
                message = input()
                if message.lower() in {"exit", "quit"}:
                    print("Exiting chat.")
                    client_socket.close()
                    break
                client_socket.sendall(f"{message}\n".encode())
        except (EOFError, KeyboardInterrupt):
            print("Exiting chat.")
            client_socket.close()

    # Thread separato per ricevere i messaggi
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()

    # Il thread principale si occupa dell'invio dei messaggi
    send_messages()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python chat.py server <port> OR python chat.py client <host:port>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == "server":
        port = int(sys.argv[2])
        start_server("0.0.0.0", port)
    elif mode == "client":
        host, port = sys.argv[2].split(":")
        start_client(host, int(port))
    else:
        print("Invalid mode. Use 'server' or 'client'.")
