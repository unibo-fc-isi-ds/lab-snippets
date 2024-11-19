from datetime import datetime
import socket
import threading
import sys
import json

class Peer:
    """
    Represents a peer in the chat.
    """
    def __init__(self, host: str, port: int, name: str = ''):
        self.host = host
        self.port = port
        self.name = name
        
    @property
    def address(self):
        return (self.host, self.port)

    def __str__(self):
        return f"{self.host}:{self.port}"
    
class ConnectedPeer(Peer):
    """
    Represents a connected peer in the chat.
    """
    def __init__(self, address, socket):
        super().__init__(*address)
        self.socket = socket

def handle_incoming_connection(peer: ConnectedPeer, peers):
    """
    Handles incoming messages from a peer.
    """
    print(f"Enstablished connection with: {peer}")
    try:
        while True:
            msg = peer.socket.recv(1024).decode()
            if not msg:
                break
            message = json.loads(msg)
            print(f"[{message['timestamp']}] {message['name']}: \n\t{message['message']}")
    except ConnectionResetError:
        print(f"Lost connection to: {peer}")
    finally:
        peer.socket.close()
        peers.remove(peer)
        print(f"{peer} <LEFT THE CHAT>")

def send_message_to_peers(peers):
    """
    Allows the user to send messages to the connected peers.
    """
    print("Type your message and press Enter to send it. Messages from other peers will be displayed below.")
    while True:
        msg = input("")
        for peer_address, peer_socket in peers:
            try:
                message = {
                    'name': local_peer.name,
                    'message': msg,
                    'timestamp': datetime.now().isoformat()
                }
                peer_socket.send(json.dumps(message).encode())
            except BrokenPipeError:
                print(f"Can't send message to: {peer_address}")

def start_peer(local_peer: Peer, peer_list: list[Peer]):
    """
    Starts the local peer and connects to the peers in the list.
    """   
    connected_peers: list[ConnectedPeer] = []

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(local_peer.address)
    server_socket.listen(5)
    print(f"Bound to: {local_peer}")

    def accept_connections():
        """
        Accepts incoming connections from peers.
        """
        while True:
            client_socket, client_address = server_socket.accept()
            client_peer = ConnectedPeer(client_address, client_socket)
            connected_peers.append(client_peer)
            threading.Thread(target=handle_incoming_connection, args=(client_peer, connected_peers)).start()

    threading.Thread(target=accept_connections, daemon=True).start()

    for peer in peer_list:
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect(peer.address)
            con_peer = ConnectedPeer(peer.address, peer_socket)
            connected_peers.append(con_peer)
            threading.Thread(target=handle_incoming_connection, args=(con_peer, connected_peers)).start()
        except ConnectionRefusedError:
            print(f"Can't connect to {peer}")

    send_message_to_peers(connected_peers)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python exercise_tcp_group_chat.py <HOST> <PORT> [<PEER_HOST:PEER_PORT> ...]")
        sys.exit(1)
        
    name = input("Enter your username to start chatting: \n")
    local_peer = Peer(sys.argv[1], int(sys.argv[2]), name)
    
    peer_list: list[Peer] = []
    for peer in sys.argv[3:]:
        attributes = peer.split(":")
        peer_list.append(Peer(attributes[0], int(attributes[1]), ''))

    start_peer(local_peer, peer_list)