import logging
import typing
from snippets.lab3 import address
import threading
import socket
from datetime import datetime
import sys
import ipaddress
from selectors import DefaultSelector, EVENT_READ
from typing import Callable
LENGTH_PREAMBLE_SIZE = 4
COMMAND_PREFIX = "/"
ENCODING = "utf-8"
BYTE_ORDER = 'big'


def is_socket_open(sock: socket.socket) -> bool:
    try:
        return sock.fileno() != -1
    except socket.error:
        return False


class Peer:
    """
    Represents a user in the chat.
    """

    def __init__(self, socket: socket.socket, name: str | None = None):
        self.socket = socket
        self.name = name

    def has_name(self) -> bool:
        return self.name != None
    
    def get_name(self) -> str:
        return self.name if self.name != None else "unknown"

    def __str__(self):
        return self.get_name() + " at " + self.socket.getpeername()


class MultiTCPChatPeer:
    logger = logging.getLogger('MultiTCPClient')
    listen_port: int

    # on_message: Callable(msg: str, sender: str) -> None
    def __init__(self, port: int, username: str, remote_endpoints: list[tuple[str, int]], on_message: Callable[[str, str], None], on_peer_connected: Callable[[str], None], on_peer_disconnected: Callable[[str], None], on_name_changed: Callable[[str, str], None]):
        """
        Initializes the client.
        Args:
            port: The port to listen for incoming connections.
            remote_endpoints: A list of [address, port] tuples of remote peers to connect to.
            on_message: A callback function that is called when a message is received. The function should take two arguments: the message and the sender's name.
            on_peer_connected: A callback function that is called when a peer connects. The function should take one argument: the peer's name.
            on_peer_disconnected: A callback function that is called when a peer disconnects. The function should take one argument: the peer's name.
            on_name_changed: A callback function that is called when a peer changes their name. The function should take two arguments: the old name and the new name.
        """
        self._thread_lock = threading.Lock()
        self.selector = DefaultSelector()
        self.remote_peers: list[Peer] = []
        self.closed: bool = False
        self.listen_port = port
        self._username = username
        self._on_message = on_message
        self._on_peer_connected = on_peer_connected
        self._on_peer_disconnected = on_peer_disconnected
        self._on_name_changed = on_name_changed
        # Create a listener socket and its thread for incoming connections
        self._newconn_listener_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self._newconn_listener_socket.bind(address(port=port))
        self._newconn_listener_thread = threading.Thread(
            target=self._handle_listener_thread, daemon=True)
        self._newconn_listener_thread.start()
        # Create a thread for receiving messages
        self._message_receiving_thread = threading.Thread(
            target=self._handle_message_receiving, daemon=True)
        self._message_receiving_thread.start()
        # Connect to remote endpoints
        for endpoint in remote_endpoints:
            # Check if the address and port are valid (if not, a ValueError will be raised)
            ipaddress.ip_address(endpoint[0])  # TODO: Add port number
            # Connect to the peer
            self.connect_to_peer(endpoint)

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value
        self._send_name_to_all(value)

    def _add_peer(self, peer: Peer):
        with self._thread_lock:
            self.remote_peers.append(peer)
            peer.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.selector.register(peer.socket, EVENT_READ)

    def remove_peer(self, peer: Peer):
        with self._thread_lock:
            if peer in self.remote_peers:
                try:
                    self._on_peer_disconnected(peer.get_name())
                    self.remote_peers.remove(peer)
                    self.selector.unregister(peer.socket)
                    peer.socket.close()
                except KeyError:
                    logging.info(
                        peer.__str__() + " was already unregistered from selector")

    def close(self):
        """
        Close the client and all its connections gracefully.
        """
        # Set the flag to stop the threads
        self.closed = True
        if threading.current_thread() is threading.main_thread():
            # Let the main thread handle the cleanup
            # Close all connections
            self._newconn_listener_socket.close()
            for peer in self.remote_peers:
                self.remove_peer(peer)
            # Wait for the threads to finish
            self._newconn_listener_thread.join()
            self._message_receiving_thread.join()
            self.selector.close()

    def _handle_listener_thread(self):
        self.logger.info(f"Listening for incoming connections on port {self.listen_port}")
        self._newconn_listener_socket.listen()
        # Start listening for peers
        try:
            while is_socket_open(self._newconn_listener_socket):
                new_socket, peer_address = self._newconn_listener_socket.accept()
                self.logger.info(
                    f"Open ingoing connection from: {peer_address}")
                new_peer = Peer(new_socket)
                self._add_peer(new_peer)
                self.logger.info(f"Connected to {peer_address}")
                self._send_name(self._username, new_peer)
        except ConnectionAbortedError as e:
            self.logger.info(f"Connection aborted: {e}")
        except (Exception, OSError) as e:
            if type(e) is OSError and e.winerror == 10038:
                # The socket was closed
                self.logger.info(
                    f"{e} (it probably means the socket was closed)")
            else:
                self.logger.error(f"Error: {e}")
        finally:
            # self.close()
            pass

    def _handle_message_receiving(self):
        while not self.closed:
            if len(self.remote_peers) != 0:
                select_res = self.selector.select(timeout=1)
                ready_sockets: list[socket.socket] = list(
                    map(lambda tuple: typing.cast(socket.socket, tuple[0][0]), select_res))
                def is_socket_ready(peer: Peer) -> bool:
                    return peer.socket in ready_sockets
                for peer in filter(is_socket_ready, self.remote_peers):
                    if is_socket_open(peer.socket):
                        try:
                            msg = self._receive(peer.socket)
                            if msg is not None:
                                if msg.startswith(COMMAND_PREFIX):
                                    # Command received
                                    match (msg.split(" "))[0]:
                                        case "/name":
                                            if peer.has_name() == False:
                                                self._on_peer_connected((msg.split(" "))[1])
                                            else:
                                                self._on_name_changed(peer.get_name() , (msg.split(" "))[1])
                                            peer.name = (msg.split(" "))[1]
                                else:
                                    # Message received
                                    self._on_message(msg, peer.get_name())
                            else:
                                self.remove_peer(peer)
                        except ConnectionResetError:
                            # Peer closed connection
                            self.logger.info(f"Connection reset by peer")
                            self.remove_peer(peer)
                            return None

    def _receive(self, socket: socket.socket):
        """
        Receives a message from a socket.
        Args:
            socket: The socket to receive the message from.
        Returns:
            The received message as a string, or None if the connection was closed.
        Raises:
            ConnectionResetError: If the connection was reset by the peer.        
        """
        # Read the length of the message
        length = int.from_bytes(socket.recv(LENGTH_PREAMBLE_SIZE), 'big')
        # If there is no message, return None
        if length == 0:
            return None
        else:
            return socket.recv(length).decode(encoding=ENCODING)

    def connect_to_peer(self, address: tuple[str, int]):
        """
        Connects to a peer.
        Args:
            address: The [address, port] of the peer to connect to.
        """
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: Check if the address is valid and add port number
        peer_socket.connect(address)
        # Send username
        new_peer = Peer(peer_socket)
        self._send_name(self._username, new_peer)
        # Add the peer to the list
        self._add_peer(new_peer)

    def _send_name_to_all(self, name: str):
        for peer in self.remote_peers:
            self._send_name(name, peer)

    def _send_name(self, name: str, peer: Peer):
        self._send_message_to_peer(COMMAND_PREFIX + "name "+name, peer)

    def send_message(self, message: str):
        for peer in self.remote_peers:
            self._send_message_to_all_peers(message, peer)

    def _send_message_to_all_peers(self, message: str, peer: Peer):
        """
        Sends a message to a peer.
        Args:
            message: The message to send.
        """
        for peer in self.remote_peers:
            self._send_message_to_peer(message, peer)
    
    def _send_message_to_peer(self, message: str, peer: Peer):
        if len(len(message).__str__()) > LENGTH_PREAMBLE_SIZE:
            # The message is too long for its length to be sent
            raise ValueError("Message too long")
        if not message.startswith(COMMAND_PREFIX):
            # The message is not a command, so prepend the timestamp and username
            message = "[" + datetime.strftime(datetime.now(),
                                                "%X %x") + "]" + self._username + ": " + message
        # Encode the message
        enc_message = message.encode(encoding=ENCODING)
        enc_message = int.to_bytes(
            len(enc_message), LENGTH_PREAMBLE_SIZE, BYTE_ORDER) + enc_message
        # Send the message to the peer
        if (is_socket_open(peer.socket)):
            try:
                peer.socket.sendall(enc_message)
            except (ConnectionResetError, ConnectionAbortedError):
                self.logger.info(f"Connection reset or aborted by peer")
                self.remove_peer(peer)
        else:
            self.remove_peer(peer)

def main():
    # Check arguments
    if len(sys.argv) < 2 or len(sys.argv) % 2 != 0:
        print(
            "Usage: python3 exercise_tcp_group_chat.py <port> [<remote_address> <remote_port> ...]")
        sys.exit(1)

    # Parse remote addresses
    remote_endpoints = []
    for i in range(2, len(sys.argv), 2):
        remote_endpoints.append((sys.argv[i], int(sys.argv[i+1])))

    # Enable logging
    logging.disable()

    # Start the client
    port = int(sys.argv[1])
    username = input("Enter your name: ")
    print("Listening for connections on port " + str(port) + "...")
    print("Type /quit to exit.")
    print("Type /name <new_name> to change your name.")
    print("Type /connect <address> <port> to connect to a peer.")
    print("---------------------------------------------")
    peer = MultiTCPChatPeer(port=port, username=username,
                            remote_endpoints=remote_endpoints,
                            on_message=lambda msg, sender: print(f"{msg}"),
                            on_peer_connected=lambda name: print(f"{name} connected"),
                            on_peer_disconnected=lambda name: print(f"{name} disconnected"),
                            on_name_changed=lambda old_name, new_name: print(f"{old_name} changed name to {new_name}"))
    try:
        while peer.closed == False:
            msg = input()
            if msg.startswith(COMMAND_PREFIX):
                match msg.split(" ")[0]:
                    case "/quit":
                        peer.close()  # Check if the command is /quit
                    case "/name":
                        peer.username = (msg.split(" "))[1]
                    case "/connect":
                        peer.connect_to_peer(
                            (msg.split(" ")[1], int(msg.split(" ")[2]))
                        )
            else:
                peer.send_message(msg)

    except (EOFError, KeyboardInterrupt):
        peer.close()

if __name__ == '__main__':
    main()