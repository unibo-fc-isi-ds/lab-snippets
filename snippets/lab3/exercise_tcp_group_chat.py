# https://unibo-fc-isi-ds.github.io/slides-module2/communication/#/exercise-tcp-group-chat

from snippets.lab3 import *
import sys
from typing import Iterable, Callable, TypeAlias


Callback: TypeAlias = Callable[[str, str | None, Connection | None, Exception | None], None]

EXIT_MESSAGE = "<LEAVES THE CHAT>"


class Peer:
    def __init__(self,
                 port: int,
                 peers: Iterable[tuple[str, int]] | None = None,
                 callback: Callback | None = None) -> None:
        self.port = port
        self.__callback = callback
        self.__peer_connections: set[Connection] = set()
        self.__listen()
        if peers is not None:
            for peer in peers:
                self.__connect_out(peer)

    def __listen(self) -> None:
        self.__listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__listener_socket.bind(address(port=self.port))
        self.__listener_thread = threading.Thread(target=self.__handle_connection_request,
                                                  daemon=True)
        if self.__callback:
            self.__listener_thread.start()

    def __handle_connection_request(self) -> None:
        self.__listener_socket.listen()
        self.on_event('listen', addr=self.__listener_socket.getsockname())
        try:
            # noinspection PyProtectedMember
            while not self.__listener_socket._closed:
                sock, addr = self.__listener_socket.accept()
                conn = Connection(sock)
                self.on_event('connect', conn, addr)
                self.__register_connection(conn)
        except ConnectionAbortedError as _:
            pass  # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')

    def __connect_out(self, peer: tuple[str, int]) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(address(port=0))
            sock.connect(peer)
            conn = Connection(sock)
            conn.callback = self.__wrap_callback(conn)
        except Exception as e:
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
                case 'close', 'error':
                    self.__forget_connection(conn)
        return wrapped_callback

    def __forget_connection(self, conn: Connection) -> None:
        self.__peer_connections.remove(conn)

    @property
    def local_address(self) -> tuple[str, int]:
        return self.__listener_socket.getsockname()

    def send_all(self, msg: str | bytes) -> None:
        if not isinstance(msg, bytes):
            msg = msg.encode()  # perform encoding here so that we do it only once
        for conn in self.__peer_connections:
            conn.send(msg)

    def on_event(self,
                 event: str,
                 conn: Connection | None = None,
                 addr: tuple[str, int] | None = None,
                 error: Exception | None = None) -> None:
        self.__callback(event, conn, addr, error)

    def close(self):
        self.__listener_socket.close()
        for conn in self.__peer_connections:
            conn.close()


def on_message_received(event: str,
                        payload: str | None,
                        conn: Connection | None,
                        error: Exception | None) -> None:
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f'Connection with peer {conn.remote_address} closed')
        case 'error':
            print(error)


local_peer = Peer(port = int(sys.argv[1]),
                  peers = [address(peer) for peer in sys.argv[2:]],
                  callback = on_message_received)

print(f'Bound to: {local_peer.local_address}')
username = input('Enter your username to start to chat:\n')
print('Type your message and press Enter to send it.')
while True:
    try:
        content = input()
        local_peer.send_all(message(content, username))
    except (EOFError, KeyboardInterrupt):
        local_peer.send_all(message(EXIT_MESSAGE, username))
        break
local_peer.close()
exit(0)  # explicit termination of the program with success
