import logging
import typing
from snippets.lab3 import address
import threading
import socket
from datetime import datetime
import sys
import ipaddress
from selectors import DefaultSelector, EVENT_READ

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

    @property
    def has_name(self) -> bool:
        return self._name != None

    @property
    def name(self) -> str:
        return self._name if self._name != None else "unknown"

    @name.setter
    def name(self, value: str | None):
        self._name: str | None = value

    def __str__(self):
        return self.name + " at " + self.socket.getpeername()


class MultiTCPChatPeer:
    logger = logging.getLogger('MultiTCPClient')
    listen_port: int

    # on_message: Callable(msg: str, sender: str) -> None
    def __init__(self, port: int, username: str, remote_endpoints: list[tuple[str, int]] = []):
        """
        Initializes the client.
        Args:
            port: The port to listen for incoming connections.
            remote_endpoints: A list of [address, port] tuples of remote peers to connect to.
        """
        self._thread_lock = threading.Lock() 
        self.selector = DefaultSelector()
        self.remote_peers: list[Peer] = []
        self.closed: bool = False
        self.listen_port = port
        self.username = username
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
            # Check if the address and port are valid
            try:
                ipaddress.ip_address(endpoint[0])
            except ValueError:
                print(f"Invalid address: {endpoint[0]}")
                continue
            if not 0 < endpoint[1] < 65536:
                print(f"Invalid port: {endpoint[1]}")
                continue
            # Connect to the peer
            self._connect_to_peer(endpoint)
        # Let main thread handle the messages sent by the user
        self._handle_message_sending()
        # When main thread finishes, close the client
        self.close()

    def add_peer(self, peer: Peer):
        with self._thread_lock:
            self.remote_peers.append(peer)
            peer.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.selector.register(peer.socket, EVENT_READ)

    def remove_peer(self, peer: Peer):
        with self._thread_lock:
            if peer in self.remote_peers:
                try:
                    print(peer.name + " disconnected")
                    self.remote_peers.remove(peer)
                    self.selector.unregister(peer.socket)
                    peer.socket.close()
                except KeyError:
                    logging.info(peer.name + " was already unregistered from selector")

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
            self.logger.info("Client closed")
            print("Client closed")

    def _handle_listener_thread(self):
        print(f"Listening for incoming connections on port {self.listen_port}")
        self._newconn_listener_socket.listen()
        # Start listening for peers
        try:
            while is_socket_open(self._newconn_listener_socket):
                new_socket, peer_address = self._newconn_listener_socket.accept()
                self.logger.info(
                    f"Open ingoing connection from: {peer_address}")
                self.add_peer(Peer(new_socket))
                self.logger.info(f"Connected to {peer_address}")
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
                for peer in filter(lambda peer: peer.socket in ready_sockets, self.remote_peers):
                    if is_socket_open(peer.socket):
                        try:
                            msg = self._receive(peer.socket)
                            if msg is not None:
                                if msg.startswith(COMMAND_PREFIX):
                                    # Command received
                                    match (msg.split(" "))[0]:
                                        case "/name":
                                            if peer.has_name == False:
                                                print((msg.split(" "))[
                                                      1] + " has joined the chat")
                                            else:
                                                print(
                                                    peer.name + " has changed their name to " + (msg.split(" "))[1])
                                            peer.name = (msg.split(" "))[1]
                                else:
                                    # Message received
                                    print(msg)  # TODO: call on_message
                            else:
                                print(peer.name + " disconnected")
                                self.remove_peer(peer)
                        except ConnectionResetError:
                            # Peer closed connection
                            self.logger.info(f"Connection reset by peer")
                            self.remove_peer(peer)
                            return None

    def _handle_message_sending(self):
        # Read messages from the user and send them to all connected peers
        while not self.closed:
            try:
                msg = input()
                if msg.startswith(COMMAND_PREFIX):
                    match msg.split(" ")[0]:
                        case "/quit":
                            self.close()  # Check if the command is /quit
                        case "/name":
                            self.username = (msg.split(" "))[1]
                            self._send_name_to_all(self.username)
                        case "/connect":
                            self._connect_to_peer(
                                (msg.split(" ")[1], int(msg.split(" ")[2])))
                else:
                    for peer in self.remote_peers:
                        self._send_message(msg, peer)
            except (EOFError, KeyboardInterrupt):
                self.close()

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

    def _connect_to_peer(self, address: tuple[str, int]):
        """
        Connects to a peer.
        Args:
            address: The [address, port] of the peer to connect to.
        """
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: Check if the address is valid and add port number
        peer_socket.connect(address)
        # Send username
        new_peer = Peer(peer_socket, "")
        self._send_name(self.username, new_peer)
        # Add the peer to the list
        self.add_peer(new_peer)

    def _send_name_to_all(self, name: str):
        for peer in self.remote_peers:
            self._send_name(name, peer)

    def _send_name(self, name: str, peer: Peer):
        self._send_message(COMMAND_PREFIX + "name "+name, peer)

    def _send_message(self, message: str, peer: Peer):
        """
        Sends a message to a peer.
        Args:
            message: The message to send.
        """
        if len(len(message).__str__()) > LENGTH_PREAMBLE_SIZE:
            # The message is too long for its length to be sent
            print("Message too long")
            return
        if not message.startswith(COMMAND_PREFIX):
            # The message is not a command, so prepend the timestamp and username
            message = "[" + datetime.strftime(datetime.now(),
                                              "%X %x") + "]" + self.username + ": " + message
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


# Check arguments
if len(sys.argv) < 2 or len(sys.argv) % 2 != 0:
    print(
        "Usage: python3 exercise_tcp_group_chat.py <port> [<remote_address> <remote_port> ...]")
    sys.exit(1)

# Parse remote addresses
remote_endpoints = []
for i in range(2, len(sys.argv), 2):
    remote_endpoints.append((sys.argv[i], int(sys.argv[i+1])))

# Start the client
port = int(sys.argv[1])
username = input("Enter your name: ")
server = MultiTCPChatPeer(port=port, username=username,
                        remote_endpoints=remote_endpoints)
