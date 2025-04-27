"""
TCP Group Chat - Daniel Meco
"""

import socket as s
import threading as th
import sys

bufferSize = 1024

# Funzioni per il Server
def start_server(host, port):
    addr = {}
    clients = {}

    def broadcast(message, sender=""):
        for client in clients:
            client.send(bytes(sender, "utf8") + message)

    def handle_client(client):
        name = client.recv(bufferSize).decode("utf8")
        welcome_message = f"Welcome {name}! Type {{exit}} to leave the chat."
        client.send(bytes(welcome_message, "utf8"))
        broadcast(bytes(f"{name} joined the chat.", "utf8"))
        clients[client] = name
        while True:
            message = client.recv(bufferSize)
            if message == bytes("{exit}", "utf8"):
                client.close()
                del clients[client]
                broadcast(bytes(f"{name} has left the chat.", "utf8"))
                break
            else:
                broadcast(message, f"{name}: ")

    server = s.socket(s.AF_INET, s.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server started on {host}:{port}")
    while True:
        client, client_addr = server.accept()
        print(f"Connection from {client_addr}")
        addr[client] = client_addr
        th.Thread(target=handle_client, args=(client,), daemon=True).start()

# Funzioni per il Client
def start_client(host, port):
    global running
    running = True

    def receive_messages():
        while running:
            try:
                message = client.recv(bufferSize).decode("utf8")
                print(message)
            except OSError:
                break

    def send_messages():
        global running  # Dichiarazione esplicita
        print("Inserisci il nome...")
        while running:
            try:
                message = input()
                client.send(bytes(message, "utf8"))
                if message == "{exit}":
                    client.close()
                    running = False
                    break
            except OSError:
                break

    client = s.socket(s.AF_INET, s.SOCK_STREAM)
    client.connect((host, port))
    print(f"Connected to server at {host}:{port}")

    th.Thread(target=receive_messages, daemon=True).start()
    send_messages()

# Main Entry Point
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python exercise_tcp_group_chat.py <server|client> <HOST> <PORT>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    host = sys.argv[2]
    port = int(sys.argv[3])

    if mode == "server":
        start_server(host, port)
    elif mode == "client":
        start_client(host, port)
    else:
        print("Invalid mode. Use 'server' or 'client'.")
        sys.exit(1)
