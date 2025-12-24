from snippets.lab2 import *
import threading
import time
import socket

class Connection:
    def __init__(self, socket: socket.socket, callback=None):
        self.__socket = socket
        self.__socket.settimeout(0.5)       # timeout anti-blocco
        self.local_address = self.__socket.getsockname()
        self.remote_address = self.__socket.getpeername()
        self.__notify_closed = False
        self.__callback = callback
        self.running = True

        self.__receiver_thread = threading.Thread(
            target=self.__handle_incoming_messages,
            daemon=True,
            name=f"Receiver-{self.remote_address}"
        )
        self.running = True
        if self.__callback:
            self.__receiver_thread.start()

    @property
    def callback(self):
        return self.__callback or (lambda *_: None)

    @callback.setter
    def callback(self, value):
        if self.__callback:
            raise ValueError("Callback can only be set once")
        self.__callback = value
        if value:
            self.__receiver_thread.start()

    @property
    def closed(self):
        return self.__socket._closed


    def send(self, message):
        if not isinstance(message, bytes):
            message = message.encode()
            message = int.to_bytes(len(message), 2, 'big') + message
        try:
            self.__socket.sendall(message)
        except OSError:
            pass

    def receive(self):
        try:
            header = self.__socket.recv(2)
            if not header:
                return None
            length = int.from_bytes(header, 'big')
            if length == 0:
                return None
            data = self.__socket.recv(length)
            if not data:
                return None
            return data.decode()
        except socket.timeout:
            return "TIMEOUT"
        except (ConnectionResetError, OSError):
            return None


    def close(self):
        self.running = False
        try:
            self.__socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.__socket.close()
        except:
            pass

        self.running = False
        if not self.__notify_closed:
            self.on_event('close')
            self.__notify_closed = True

    def __handle_incoming_messages(self):
        try:
            while self.running and not self.closed:
                message = self.receive()
                if message == "TIMEOUT":
                    continue
                if message is None:
                    break
                self.on_event('message', message)


        except Exception as e:
            if self.closed and isinstance(e, OSError):
                return
                return
            self.on_event('error', error=e)
        finally:
            self.close()

    def on_event(self, event: str, payload: str=None, connection: 'Connection'=None, error: Exception=None):
        if connection is None:
            connection = self
        self.callback(event, payload, connection, error)

class Client(Connection):
    def __init__(self, server_address, callback=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.settimeout(0.5)
        sock.bind(address(port=0))
        sock.connect(address(*server_address))
        super().__init__(sock, callback)

class Server:
    def __init__(self, port, callback=None):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.settimeout(0.5)
        self.__socket.settimeout(0.5)
        self.__socket.bind(address(port=port))
        self.__callback = callback
        self.running = True

        self.__listener_thread = threading.Thread(
            target=self.__handle_incoming_connections,
            daemon=True,
            name=f"ServerListener-{port}"
        )
        self.running = True
        if self.__callback:
            self.__listener_thread.start()

    @property
    def callback(self):
        return self.__callback or (lambda *_: None)


    @callback.setter
    def callback(self, value):
        if self.__callback:
            raise ValueError("Callback can only be set once")
        self.__callback = value
        if value:
            self.__listener_thread.start()


    def __handle_incoming_connections(self):
        self.__socket.listen()
        self.on_event('listen', address=self.__socket.getsockname())
        try:
            while self.running and not self.__socket._closed:
                try:
                    s, address = self.__socket.accept()
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.__socket._closed:
                        break
                    else:
                        self.on_event('error', error=e)
                        break
                connection = Connection(s)
                self.on_event('connect', connection, address)
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')

    def on_event(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None):
        self.__callback(event, connection, address, error)

    def close(self):
        self.running = False
        try:
            self.__socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.__socket.close()
        except:
            pass

class Peer:
    def __init__(self, username, listen_port, other_peers):
        self.username = username
        self.listen_port = listen_port
        self.other_peers = other_peers

        self.connections = []
        self.lock = threading.Lock()
        self.running = True
        self.closing = False

        self.server = Server(listen_port, self.__on_server_event)

        for peer_addr in self.other_peers:
            self.connect_to_peer(peer_addr)

    def connect_to_peer(self, addr):
        try:
            conn = Client(address(*addr), self.__on_connection_event)
            with self.lock:
                self.connections.append(conn)
            conn.send(f"{self.username} has joined the chat")
        except Exception as e:
            print(f"Connection failed with {addr}: {e}")

    def __on_server_event(self, event, connection, address, error):
        if event == "connect":
            connection.callback = self.__on_connection_event
            with self.lock:
                self.connections.append(connection)
            connection.send(f"{self.username} has joined the chat")
        elif event == "listen":
            print(f"> Server listening on {address}")
        elif event == "error":
            print("Server error:", error)

    def __on_connection_event(self, event, payload, connection, error):
        if self.closing:
            return
        if event == "message":
            print(payload)
        elif event == "close":
            with self.lock:
                if connection in self.connections:
                    self.connections.remove(connection)
        elif event == "error":
            print("Error:", error)

    def broadcast(self, message):
        with self.lock:
            for c in list(self.connections):
                try:
                    c.send(message)
                except:
                    pass

    def close(self):
        self.closing = True
        self.running = False
        try:
            self.broadcast(f"{self.username} has left the chat")
            time.sleep(0.05)
        except:
            pass
        with self.lock:
            for c in list(self.connections):
                try:
                    c.close()
                except:
                    pass
            self.connections.clear()
        try:
            self.server.close()
        except:
            pass
        time.sleep(0.05)
