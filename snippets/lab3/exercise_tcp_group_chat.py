from dataclasses import dataclass, field
from snippets.lab3 import Server, Client, address, message, local_ips
import sys

@dataclass
class TCPPeer:
    def __init__(self, port:int, remote_endpoints=None):
        self._port = port
        self._server = Server(self._port, self.on_new_connection)
        self._remote_peers = []
        self._remote_endpoints = remote_endpoints if remote_endpoints is not None else []
        self.initialize_connections()

    def initialize_connections(self):
        for endpoint in self._remote_endpoints:
            self.connect_to_peer(endpoint)

    def send_message(self, msg, sender):
        if not self._remote_peers:
            print("No peers connected, message is lost")
        elif msg:
            for peer in self._remote_peers:
                peer.send(message(msg.strip(), sender))
        else:
            print("Empty message, not sent")

    def on_message_received(self, event, payload, connection, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                print(f"Connection with peer {connection.remote_address} closed")
                if connection in self._remote_peers:
                    self._remote_peers.remove(connection)
            case 'error':
                print(error)

    def on_new_connection(self, event, connection, address, error):
        match event:
            case 'listen':
                print(f"Listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open connection from: {address}")
                connection.callback = self.on_message_received
                self._remote_peers.append(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

    def connect_to_peer(self, remote_endpoint):
        peer = Client(address(remote_endpoint), self.on_message_received)
        self._remote_peers.append(peer)
        print(f"Connected to {peer.remote_address}")

    def close(self):
        for peer in self._remote_peers:
            peer.close()
        self._server.close()

port = int(sys.argv[1])
remote_endpoints = sys.argv[2:]  # Lista di endpoint remoti
peer = TCPPeer(port, remote_endpoints)

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        peer.send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        peer.close()
        break