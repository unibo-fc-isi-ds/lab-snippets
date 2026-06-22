from snippets.lab3 import *
import sys
import threading

EXIT_MESSAGE = "<LEAVES THE CHAT>"

class TCPGroupChat:
    def __init__(self, port, peers=[]):
        self.peers = []
        self.lock = threading.Lock()
        self.server = Server(port, self.on_new_connection)
        
        for peer_addr in peers:
            try:
                client = Client(address(peer_addr), self.on_message_received)
                with self.lock:
                    self.peers.append(client)
                print(f"Connected to {client.remote_address}")
            except Exception as e:
                print(f"Failed to connect to {peer_addr}: {e}")

    def on_new_connection(self, event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Accepted connection from: {address}")
                connection.callback = self.on_message_received
                with self.lock:
                    self.peers.append(connection)
            case 'stop':
                print("Server stopped")
            case 'error':
                print(f"Server error: {error}")

    def on_message_received(self, event, payload, connection, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                print(f"Connection with {connection.remote_address} closed")
                with self.lock:
                    if connection in self.peers:
                        self.peers.remove(connection)
            case 'error':
                print(f"Error with peer {connection.remote_address}: {error}")

    def broadcast(self, msg, sender):
        formatted_msg = message(msg.strip(), sender)
        with self.lock:
            current_peers = list(self.peers)
        
        for peer in current_peers:
            try:
                peer.send(formatted_msg)
            except Exception as e:
                print(f"Failed to send to {peer.remote_address}: {e}")

    def close(self):
        self.server.close()
        with self.lock:
            peers_to_close = list(self.peers)
        
        for peer in peers_to_close:
            peer.close()


if len(sys.argv) < 2:
    print(f"Usage: python -m snippets.lab3.exercise_tcp_group_chat <port> [peer_address1 peer_address2 ...]")
    sys.exit(1)

port = int(sys.argv[1])
initial_peers = sys.argv[2:]

chat = TCPGroupChat(port, initial_peers)

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

while True:
    try:
        content = input()
        chat.broadcast(content, username)
    except (EOFError, KeyboardInterrupt):
        chat.broadcast(EXIT_MESSAGE, username)
        break

chat.close()
sys.exit(0)