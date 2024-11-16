from snippets.lab3 import Server, Client, Connection, address, message, local_ips
from typing import TypeAlias
import sys
import logging

Message: TypeAlias = str
Username: TypeAlias = str
Port: TypeAlias = int
Endpoints: TypeAlias = list[str]

class TCPPeer:
    def __init__(self, port: Port, remote_endpoints: Endpoints | None = None):
        self.__port = port
        self.__server = Server(self.__port, self.__on_new_connection)
        self.__remote_peers = list()
        self.__initialize_connections(remote_endpoints if remote_endpoints is not None 
                                                       else list())

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
        msg = f"Connected to {peer.remote_address}"
        print(msg)
        logging.info(msg)

    def __on_message_received(self, 
                              event: str, 
                              payload: str, 
                              connection: Connection, 
                              error: str) -> None:
        match event:
            case 'message':
                print(payload)
                logging.info(f"FROM({connection.remote_address}): {payload}")
            case 'close':
                msg = f"Connection with peer {connection.remote_address} closed"
                self.__remote_peers.remove(connection)
                print(msg)
                logging.info(msg)
            case 'error':
                print(error)
                logging.error(error)

    def __on_new_connection(self, 
                            event: str, 
                            connection: Connection, 
                            address: tuple[str, int], 
                            error: str) -> None:
        match event:
            case 'listen':
                print(f"Listening on port {address[0]} at {', '.join(local_ips())}")
                logging.info(f"Peer created @ ({address[0]}:{address[1]})")
            case 'connect':
                msg = f"Open connection from: {address}"
                print(msg)
                connection.callback = self.__on_message_received
                self.__remote_peers.append(connection)
                logging.info(msg)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)
                logging.error(error)

if __name__ == '__main__':
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