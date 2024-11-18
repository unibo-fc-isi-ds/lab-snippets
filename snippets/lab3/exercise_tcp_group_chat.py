from snippets.lab3 import *
from typing import List
import sys
import socket

EXIT_MESSAGE = "<HAS LEFT THE CHAT>"

class TCPPeer:
    def __init__(self, username, server_port, endpoints: List[str]=[]):
        self.__username = username
        self.__server = Server(server_port, self.__on_new_connection)
        self.__peers: List[Client] = []
        for endpoint in endpoints:
            try:
                self.__peers.append(Client(address(endpoint), self.__on_message_received))
            except socket.error as e:
                print(f"Failed to connect to {endpoint}, ignoring... ({e})")
        if self.peers_count > 0:
            print(f"Connected to:")
            for peer in self.__peers:
                print(f"- {peer.remote_address}")

    def __on_message_received(self, event, payload, connection: Connection, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                print(f"Connection with peer {connection.remote_address} closed")
                self.__peers = list(filter(lambda p : p.remote_address != connection.remote_address, self.__peers))
            case 'error':
                print(error)

    def __on_new_connection(self, event, connection: Connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open inbound connection from: {address}")
                connection.callback = self.__on_message_received
                self.__peers.append(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

    @property
    def peers_count(self):
        return len(self.__peers)

    def broadcast(self, msg):
        if self.peers_count == 0:
            print("No peer connected, message is lost")
        elif msg:
            for peer in list(self.__peers):
                try:
                    peer.send(message(msg.strip(), self.__username))
                except socket.error as e:
                    self.__peers.remove(peer)
                    print(f"Failed to deliver message to {peer.remote_address} ({e}). Peer removed.")
        else:
            print("Empty message, not sent")

    def close_all_connections(self):
        self.__server.close()
        for peer in self.__peers:
            peer.close()

if __name__ == "__main__":
    username = input('Enter your username to start the chat:\n')
    peer = TCPPeer(username, server_port=int(sys.argv[1]), endpoints=sys.argv[2:])
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
    while True:
        try:
            content = input()
            peer.broadcast(content)
        except (EOFError, KeyboardInterrupt):
            print("Leaving the chat...")
            if peer.peers_count > 0:
                peer.broadcast(EXIT_MESSAGE)
            break
    peer.close_all_connections()
    exit(0)
