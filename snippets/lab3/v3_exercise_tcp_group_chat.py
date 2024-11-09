import sys
import threading    
from datetime import datetime
import psutil
import socket
import time

def address(ip='0.0.0.0:0', port=None):
    ip = ip.strip()
    if ':' in ip:
        ip, p = ip.split(':')
        p = int(p)
        port = port or p
    if port is None:
        port = 0
    assert port in range(0, 65536), "Port number must be in the range 0-65535"
    assert isinstance(ip, str), "IP address must be a string"
    return ip, port

def message(text: str, sender: str, timestamp: datetime=None):
    if timestamp is None:
        timestamp = datetime.now()
    return f"[{timestamp.isoformat()}] {sender}:\n\t{text}"


def local_ips():
    for interface in psutil.net_if_addrs().values():
        for addr in interface:
            if addr.family == socket.AF_INET:
                    yield addr.address

class Connection:
    def __init__(self, socket: socket.socket, callback=None):
        self.__socket = socket
        self.local_address = self.__socket.getsockname()
        self.remote_address = self.__socket.getpeername()
        self.__notify_closed = False
        self.__callback = callback
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
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
        self.__socket.sendall(message)

    def receive(self):
        length = int.from_bytes(self.__socket.recv(2), 'big')
        if length == 0:
            return None
        return self.__socket.recv(length).decode()
    
    def close(self):
        self.__socket.close()
        if not self.__notify_closed:
            self.on_event('close', connection=self)
            self.__notify_closed = True

    def __handle_incoming_messages(self):
        try:
            while not self.closed:
                message = self.receive()
                if message is None:
                    break
                self.on_event('message', message)
        except Exception as e:
            if self.closed and isinstance(e, OSError):
                return # silently ignore error, because this is simply the socket being closed locally
            self.on_event('error', error=e)
        finally:
            self.close()

    def on_event(self, event: str, payload: str=None, connection: 'Connection'=None, error: Exception=None):
        if connection is None:
            connection = self
        self.callback(event, payload, connection, error)
#### Connection Class ends here


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
        self.__callback = callback
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
            while not self.__socket._closed:
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
#### Server Class ends here

# Each peer acts as both a server and a client
class ChatPeer:
    def __init__(self, port, username):
        self.server = Server(port, self.on_new_connection)
        self.username = username
        self.clients = []
        self.peer_writing = []

    def connect_to_peer(self, peer_address):
        client = Client(peer_address, self.on_message_received)
        self.clients.append(client)
        
    # deamon for keyboard input
    def send_messages(self):
        while True:
            msg = input()
            for clients in self.clients:
                print(f"{username}: Sending: '{msg}',  to client: ", clients.remote_address)
                clients.send(message(msg.strip(), self.username))

    # def start_chat(self):
    #     threading.Thread(target=self.send_messages, daemon=True).start()

    def on_message_received(self, event, payload, connection, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                # remove remote peer from the list
                print(f"{username}: Connection with peer {connection.remote_address} closed")
                peer_to_remove = [peer for peer in self.peer_writing if peer.remote_address == connection.remote_address]
                for peer in peer_to_remove:
                    print(f"{username}: A peer jus disconnected: ", peer.remote_address)
                    self.peer_writing.remove(peer)
            case 'error':
                print(error)


    def on_new_connection(self, event, connection, address, error):
            match event:
                case 'listen':
                    print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
                case 'connect':
                    # add remote peer to the list
                    print(f"Open ingoing connection from: {address}")
                    connection.callback = self.on_message_received
                    self.peer_writing.append(connection)
                    # self.clients.append(Client (address, self.on_message_received))
                case 'stop':
                    print(f"Stop listening for new connections")
                case 'error':
                    print(error)

if __name__ == "__main__":
    # Initialize the peer as a server on the specified port
    
    username = sys.argv[1]
    port = int(sys.argv[2])
    remote_endpoints = [address(endp) for endp in sys.argv[3:]]

    peer = ChatPeer(port, username)
    time.sleep(2) # wait for the serves to start
    
    for endpoint in remote_endpoints:
        peer.connect_to_peer(endpoint)
    peer.send_messages()