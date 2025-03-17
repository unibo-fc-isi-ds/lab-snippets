from snippets.lab3 import Server, Client, Connection, address, local_ips
from typing import TypeAlias
from datetime import datetime
import sys
import logging

DEBUG_MODE = True

Message: TypeAlias = str
Username: TypeAlias = str
Port: TypeAlias = int
Endpoints: TypeAlias = list[str]

def make_message(text: str, sender: str, timestamp=None) -> str:
    if DEBUG_MODE:
        return f"{sender}#{text}"
    if timestamp is None:
        timestamp = datetime.now()
    return f"[{timestamp.isoformat()}] {sender}:\n\t{text}"

class TCPPeer:
    def __init__(self,
                 username: Username, 
                 port: Port, 
                 remote_endpoints: Endpoints | None = None):
        self.username = username
        self.__port = port
        self.__server = Server(self.__port, self.__on_new_connection)
        self.__remote_peers = list()
        self.__initialize_connections(remote_endpoints if remote_endpoints is not None 
                                                       else list())

    def send_message(self, msg: Message) -> None:
        if not self.__remote_peers:
            print("No peers connected, message is lost")
        elif msg:
            for peer in self.__remote_peers:
                payload = make_message(msg.strip(), self.username)
                peer.send(payload)
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
                # * Not the greatest design, but it's okay for now...
                if not DEBUG_MODE:
                    print(payload)
                    return
                remote_peer_username, msg = payload.split("#")
                logging.info(f"{remote_peer_username} -> {self.username}: {msg}")
                print(f"{remote_peer_username}: {msg}")
            case 'close':
                if connection in self.__remote_peers:
                    self.__remote_peers.remove(connection)
                print(f"Connection with peer {connection.remote_address} closed")
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

if __name__ == '__main__':
    DEBUG_MODE = False
    port = int(sys.argv[1])
    remote_endpoints = sys.argv[2:]
    username = input('Enter your username to start the chat:\n')

    peer = TCPPeer(username, port, remote_endpoints)

    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
    while True:
        try:
            msg = input()
            peer.send_message(msg)
        except (EOFError, KeyboardInterrupt):
            peer.close()
            break
    exit(0)

# ? How to run?
# Peer 0
# poetry run python -m snippets -l 3 -e tcp_group_chat 8080
# Peer 1, 2, etc.
# poetry run python -m snippets -l 3 -e tcp_group_chat 8082 localhost:8080 localhost:8081