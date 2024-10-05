from snippets.lab2 import *
import threading


# Uncomment this line to observe timeout errors more often.
# Beware: short timeouts can make demonstrations more difficult to follow.
# socket.setdefaulttimeout(5) # set default timeout for blocking operations to 5 seconds


class Connection:
    def __init__(self, socket: socket.socket, callback=None):
        self.__socket = socket
        self.local_address = self.__socket.getsockname()
        self.remote_address = self.__socket.getpeername()
        self.__closed = False
        self.callback = callback or (lambda *_: None)
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        self.__receiver_thread.start()
    
    def send(self, message):
        if not isinstance(message, bytes):
            message = message.encode()
            message = int.to_bytes(len(message), 2, 'big') + message
        self.__socket.sendall(message)

    def receive(self):
        length = int.from_bytes(self.__socket.recv(2), 'big')
        if length == 0:
            return None
        return self.__socket.recv(length).decode()
    
    def close(self):
        should_emit_event = False
        if not self.__closed:
            self.__closed = True
            should_emit_event = True
        self.__socket.close()
        if should_emit_event:
            self.on_event('close')

    def __handle_incoming_messages(self):
        try:
            while True:
                message = self.receive()
                if message is None:
                    break
                self.on_event('message', message)
        except Exception as e:
            if self.__closed and isinstance(e, OSError):
                return # silently ignore error, because this is simply the socket being closed locally
            self.on_event('error', error=e)
        finally:
            self.__closed = True
            self.on_event('close')

    def on_event(self, event: str, payload: str=None, sender: tuple=None, error: Exception=None):
        if sender is None:
            sender = self.remote_address
        self.callback(event, payload, sender, error)


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
        self.on_event('listen', address=self.__socket.getsockname())
        try:
            while True:
                socket, address = self.__socket.accept()
                connection = Connection(socket)
                self.on_event('connect', connection, address)
        except ConnectionAbortedError as e:
            pass # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')

    def on_event(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None):
        self.__callback(event, connection, address, error)

    def close(self):
        self.__socket.close()
