import socket
import threading


class Peer:
    def __init__(self, mode, address=None, port=None, callback=None):
        self.mode = mode
        self.callback = callback or (lambda *args: None)
        self.local_address = (socket.gethostbyname(socket.gethostname()), port)
        self.peers = set()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connections = {}  
        if mode == "server":
            self.start_as_server(port)
        elif mode == "client":
            self.join_chat(address)

    def start_as_server(self, port):
        self.server_socket.bind(("0.0.0.0", port))
        self.server_socket.listen()
        print(f"Server listening at {self.local_address}")
        threading.Thread(target=self.handle_incoming_connections, daemon=True).start()
        self.peers.add(self.local_address)  

    def join_chat(self, server_address):
        server_ip, server_port = server_address.split(":")
        server_endpoint = (server_ip, int(server_port))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(server_endpoint)
        self.connections[server_endpoint] = client_socket
        self.peers.add(server_endpoint)  # Add the server to the peer list
        self.local_address = client_socket.getsockname()  # Correctly assign local address and port
        print(f"Connected to chat at {server_endpoint}")
        threading.Thread(target=self.listen_for_messages, args=(client_socket,), daemon=True).start()
        self.send_message("NEW_JOIN", self.local_address)

    def handle_incoming_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            if client_address not in self.connections:
                self.connections[client_address] = client_socket
                print(f"New connection from {client_address}")
                self.peers.add(client_address)
                threading.Thread(target=self.handle_peer, args=(client_socket, client_address), daemon=True).start()

    def handle_peer(self, client_socket, client_address):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if message:
                    self.process_message(message, client_address)
            except:
                break
        client_socket.close()
        del self.connections[client_address]
        self.peers.discard(client_address)

    def listen_for_messages(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if message:
                    self.process_message(message, None)
            except:
                break

    def process_message(self, message, sender_address):
        if message.startswith("NEW_JOIN"):
            _, new_peer = message.split(",", 1)
            new_peer = eval(new_peer)
            if new_peer != self.local_address and new_peer[1] is not None: 
                self.peers.add(new_peer)
                self.broadcast_peer_list()
        elif message.startswith("PEER_LIST"):
            _, peer_list = message.split(",", 1)
            self.peers.update(eval(peer_list))
            self.peers.discard(self.local_address)  
            print(f"Updated peers: {self.peers}")
        elif message.startswith("CHAT"):
            _, chat_message = message.split(",", 1)
            self.callback("message", chat_message)
            if sender_address:  
                self.broadcast_message("CHAT", chat_message, exclude=sender_address)
        else:
            self.callback("message", message)

    def send_message(self, message_type, payload):
        message = f"{message_type},{payload}"
        for peer in list(self.peers):
            if peer in self.connections:
                try:
                    self.connections[peer].sendall(message.encode())
                except Exception as e:
                    print(f"Failed to send message to {peer}: {e}")

    def broadcast_peer_list(self):
        self.send_message("PEER_LIST", list(self.peers))

    def broadcast_message(self, message_type, payload, exclude=None):
        message = f"{message_type},{payload}"
        for peer in list(self.peers):
            if peer != exclude and peer in self.connections:
                try:
                    self.connections[peer].sendall(message.encode())
                except Exception as e:
                    print(f"Failed to broadcast message to {peer}: {e}")

    def send_chat_message(self, message):
        self.send_message("CHAT", message)
