# https://unibo-fc-isi-ds.github.io/slides-module2/communication/#/exercise-tcp-group-chat


import traceback

from snippets.lab3 import *
import sys
from typing import Iterable, Callable, TypeAlias


INFO_MODE = 0

Address: TypeAlias = tuple[str, int]

# arguments expected by the Connection class
Callback: TypeAlias = Callable[[
    str,  # event
    str | None,  # payload
    Connection | None,  # connection
    Exception | None  # error
], None]

ListenCallback: TypeAlias = Callable[[
    str,  # event
    Connection | None,  # connection
    Address | None,  # address
    Exception | None  # error
], None]

JOIN_MESSAGE = '<JOINS THE CHAT>'
EXIT_MESSAGE = '<LEAVES THE CHAT>'


def info_print(*values: object, sep: str | None = ' ', end: str | None = '\n', level: int = 1) -> None:
    if INFO_MODE >= level:
        print(*values, sep=sep, end=end)


class Peer:
    def __init__(self,
                 port: int,
                 peers: Iterable[Address] | None = None,
                 callback: Callback | None = None,
                 listen_callback: ListenCallback | None = None) -> None:
        self.port = port
        self.__callback = callback
        self.__listen_callback = listen_callback
        self.__peer_connections: set[Connection] = set()
        self.__listen()
        if peers is not None:
            for peer in peers:
                self.__connect_out(peer)

    def __listen(self) -> None:
        self.__listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__listener_socket.bind(address(port=self.port))
        self.__listener_thread = threading.Thread(target=self.__handle_connection_request,
                                                  daemon=False)
        if self.__callback and self.__listen_callback:
            self.__listener_thread.start()

    @property
    def listen_closed(self):
        # noinspection PyProtectedMember
        return self.__listener_socket._closed

    def __handle_connection_request(self) -> None:
        self.__listener_socket.listen()
        self.on_listen_event('listen', addr=self.__listener_socket.getsockname())
        try:
            while not self.listen_closed:
                sock, addr = self.__listener_socket.accept()
                conn = Connection(sock)
                self.on_listen_event('connect', conn, addr)
                self.__register_connection(conn)
        except Exception as e:
            if self.listen_closed and isinstance(e, OSError):
                return  # silently ignore error, because this is simply the socket being closed locally
            self.on_event('error', error=e)
        finally:
            self.on_listen_event('stop')

    def __connect_out(self, peer: Address) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(address(port=0))
            sock.connect(peer)
            conn = Connection(sock)
            self.on_event('connect', conn=conn)
        except Exception as e:
            info_print(f'Failed to connect to peer {peer}')
            self.on_event('error', error=e)
        else:
            self.__register_connection(conn)

    def __register_connection(self, conn: Connection) -> None:
        conn.callback = self.__wrap_callback(conn)
        self.__peer_connections.add(conn)

    def __wrap_callback(self, conn: Connection) -> Callback:
        def wrapped_callback(event: str,
                             payload: bytes | None,
                             connection: Connection | None,
                             error: Exception | None) -> None:
            self.__callback(event, payload, connection, error)
            match event:
                case 'close':
                    self.__forget_connection(conn)
        return wrapped_callback

    def __forget_connection(self, conn: Connection) -> None:
        self.__peer_connections.remove(conn)

    @property
    def local_address(self) -> Address:
        return self.__listener_socket.getsockname()

    @property
    def connections(self) -> int:
        return len(self.__peer_connections)

    def send_all(self, msg: str | bytes) -> None:
        if not isinstance(msg, bytes):
            msg = msg.encode()  # perform encoding here so that we do it only once
            msg = int.to_bytes(len(msg), 2, 'big') + msg
        for conn in self.__peer_connections:
            conn.send(msg)

    def on_event(self,
                 event: str,
                 payload: str | None = None,
                 conn: Connection | None = None,
                 error: Exception | None = None) -> None:
        self.__callback(event, payload, conn, error)

    def on_listen_event(self,
                        event: str,
                        conn: Connection | None = None,
                        addr: Address | None = None,
                        error: Exception | None = None) -> None:
        self.__listen_callback(event, conn, addr, error)

    def graceful_close_all(self) -> None:
        for conn in self.__peer_connections.copy():
            # noinspection PyUnresolvedReferences, PyProtectedMember
            conn._Connection__socket.shutdown(socket.SHUT_RDWR)  # try graceful shutdown
            conn.close()  # at the end, force close
        self.__listener_socket.close()


def send_message(msg: str, sender: str) -> None:
    if msg:
        local_peer.send_all(message(msg.strip(), sender))
    else:
        print('Empty message, not sent')

def on_message_received(event: str,
                        payload: str | None,
                        conn: Connection | None,
                        error: Exception | None) -> None:
    match event:
        case 'message':
            print(payload)
        case 'connect':
            info_print(f'Connected to peer {conn.remote_address}')
        case 'close':
            info_print(f'Connection with peer {conn.remote_address} closed')
        case 'error':
            info_print(error)
            info_print(traceback.format_exc(), level=2)

# noinspection PyUnusedLocal
def on_new_connection(event: str,
                      conn: Connection | None,
                      addr: Address | None,
                      error: Exception | None) -> None:
    match event:
        case 'listen':
            info_print(f'Listening on port {addr[0]}')
        case 'connect':
            info_print(f'Accepted connection from {addr}')
        case 'stop':
            info_print(f'Stopped listening for new connections')
        case 'error':
            info_print(error)
            info_print(traceback.format_exc(), level=2)


username = input('Enter your username to start to chat:\n')

local_peer = Peer(port=int(sys.argv[1]),
                  peers=[address(peer) for peer in sys.argv[2:]],
                  callback=on_message_received,
                  listen_callback=on_new_connection)

info_print(f'Bound to: {local_peer.local_address}')
print(f'There are {local_peer.connections} connected users')
send_message(JOIN_MESSAGE, username)
print('Type your message and press Enter to send it. Messages from other users will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        send_message(EXIT_MESSAGE, username)
        break
local_peer.graceful_close_all()
exit(0)
