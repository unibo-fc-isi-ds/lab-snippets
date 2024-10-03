from snippets.lab2 import *
import threading
import sys


class Connection:
    def __init__(self, socket: socket.socket, callback=None):
        self.__socket = socket
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        self.callback = callback or (lambda *_: None)
        self.__receiver_thread.start()
    
    @property
    def local_address(self):
        return self.__socket.getsockname()
    
    @property
    def remote_address(self):
        return self.__socket.getpeername()
    
    @property
    def callback(self):
        return self.__callback

    @callback.setter
    def callback(self, value):
        assert callable(value), "Callback must be a callable object"
        self.__callback = value
    
    def send(self, message):
        if not isinstance(message, bytes):
            message = message.encode()
            message = int.to_bytes(len(message), 2, 'big') + message
        self.__socket.send(message)

    def receive(self):
        length = int.from_bytes(self.__socket.recv(2), 'big')
        return self.__socket.recv(length).decode()
    
    def close(self):
        self.__socket.close()

    def __handle_incoming_messages(self):
        while True:
            message = self.receive()
            self.on_message_received(message)

    def on_message_received(self, payload):
        self.callback(payload)


class Client(Connection):
    def __init__(self, server_address, callback=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(address(port=0))
        sock.connect(address(*server_address))
        super().__init__(sock, callback)


class Server:
    def __init__(self, port, callback=None):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(address(port=port))
        self.__listener_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True)
        self.__callback = callback or (lambda *_: None)
        self.__listener_thread.start()
    
    def __handle_incoming_connections(self):
        self.__socket.listen()
        while True:
            connection, address = self.__socket.accept()
            connection = Connection(connection, self.on_connection_received)
            self.on_connection_received(connection, address)

    def on_connection_received(self, connection, address):
        self.__callback(connection, address)
    