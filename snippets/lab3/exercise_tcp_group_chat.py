from snippets.lab3 import Server, Client, Connection, address, message, local_ips
from typing import TypeAlias
import sys

Message: TypeAlias = str
Username: TypeAlias = str
Port: TypeAlias = int
Endpoints: TypeAlias = list[str]

class TCPPeer:
    def __init__(self, port: Port, remote_endpoints: Endpoints | None = None):
        self.__port = port
        self.__server = Server(self.__port, self.__on_new_connection)
        self.__remote_peers = list()
        self.__initialize_connections(remote_endpoints)

    def send_message(self, msg: Message, sender: Username) -> None:
        if not self.__remote_peers:
            print("No peers connected, message is lost")
        elif msg:
            for peer in self.__remote_peers:
                peer.send(message(msg.strip(), sender))
        else:
            print("Empty message, not sent")

    def close(self) -> None:
        for peer in self.__remote_peers:
            peer.close()
        self.__server.close()

    def __initialize_connections(self, remote_endpoints: list[str]) -> None:
        for endpoint in remote_endpoints:
            self.__connect_to_peer(endpoint)

    def __connect_to_peer(self, remote_endpoint: str) -> None:
        peer = Client(address(remote_endpoint), self.__on_message_received)
        self.__remote_peers.append(peer)
        print(f"Connected to {peer.remote_address}")

    def __on_message_received(self, 
                              event: str, 
                              payload: str, 
                              connection: Connection, 
                              error: str) -> None:
        match event:
            case 'message':
                print(payload)
            case 'close':
                print(f"Connection with peer {connection.remote_address} closed")
                self.__remote_peers.remove(connection)
            case 'error':
                print(error)

    def __on_new_connection(self, 
                            event: str, 
                            connection: Connection, 
                            address: tuple[str, int], 
                            error: str) -> None:
        match event:
            case 'listen':
                print(f"Listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open connection from: {address}")
                connection.callback = self.__on_message_received
                self.__remote_peers.append(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

port = int(sys.argv[1])
remote_endpoints = sys.argv[2:]
peer = TCPPeer(port, remote_endpoints)

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        msg = input()
        peer.send_message(msg, username)
    except (EOFError, KeyboardInterrupt):
        peer.close()
        break