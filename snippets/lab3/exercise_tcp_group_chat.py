import sys
import threading
from typing import List, Tuple, Set
from snippets.lab3 import Client, Server, address, local_ips, message


class ConnectionManager:
    """Manages peer connections in a thread-safe manner"""

    def __init__(self):
        self._connections: List[Client] = []
        self._known_endpoints: Set[Tuple] = set()
        self._mutex = threading.Lock()

    def register(self, connection: Client) -> bool:
        """Register a new connection if not already present"""
        with self._mutex:
            endpoint = connection.remote_address
            if endpoint in self._known_endpoints:
                return False
            self._connections.append(connection)
            self._known_endpoints.add(endpoint)
            return True

    def unregister(self, connection: Client):
        """Remove a connection from tracking"""
        with self._mutex:
            if connection in self._connections:
                self._connections.remove(connection)
                self._known_endpoints.discard(connection.remote_address)

    def list_all(self) -> List[Client]:
        """Get snapshot of current connections"""
        with self._mutex:
            return list(self._connections)

    def shutdown(self):
        """Close all managed connections"""
        with self._mutex:
            for conn in self._connections:
                try:
                    conn.close()
                except:
                    pass
            self._connections.clear()
            self._known_endpoints.clear()


def validate_cli_args():
    """Validate and parse command line arguments"""
    if len(sys.argv) < 2:
        print("USAGE: poetry run python -m snippets.lab3.exercise_tcp_group_chat PORT [PEER_HOST:PORT ...]")
        print("Example: poetry run python -m snippets.lab3.exercise_tcp_group_chat 5000 localhost:5001")
        sys.exit(1)

    try:
        listen_port = int(sys.argv[1])
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError("Port should be between 1024-65535")
    except ValueError as err:
        print(f"ERROR: Invalid port number - {err}")
        sys.exit(1)

    initial_peers = []
    for peer_spec in sys.argv[2:]:
        try:
            initial_peers.append(address(peer_spec))
        except:
            print(f"WARNING: Skipping invalid peer address: {peer_spec}")

    return listen_port, initial_peers


def distribute_message(text: str, nickname: str, conn_manager: ConnectionManager):
    """Distribute message to all active connections"""
    if not text.strip():
        print("[!] Cannot send empty message")
        return

    active_connections = conn_manager.list_all()
    if not active_connections:
        print("[!] No active connections")
        return

    msg_content = message(text.strip(), nickname)
    failed = []

    for conn in active_connections:
        try:
            conn.send(msg_content)
        except Exception:
            print(f"[!] Failed to deliver to {conn.remote_address[0]}:{conn.remote_address[1]}")
            failed.append(conn)

    for conn in failed:
        conn_manager.unregister(conn)


def build_message_handler(conn_manager: ConnectionManager):
    """Build handler for incoming messages"""

    def handle_message(event_type: str, data: str, conn: Client, err: str):
        if event_type == "message":
            print(f"{data}")
        elif event_type == "close":
            print(f"[*] Disconnected from {conn.remote_address[0]}:{conn.remote_address[1]}")
            conn_manager.unregister(conn)
        elif event_type == "error":
            print(f"[!] Connection error: {err}")
            conn_manager.unregister(conn)

    return handle_message


def build_accept_handler(conn_manager: ConnectionManager, msg_handler):
    """Build handler for accepting connections"""

    def handle_accept(event_type: str, conn: Client, addr: List, err: str):
        if event_type == "listen":
            local_addrs = ', '.join(local_ips())
            print(f"[*] Listening on {addr[0]} ({local_addrs})")
        elif event_type == "connect":
            print(f"[+] Accepted connection from {addr[0]}:{addr[1]}")
            conn.callback = msg_handler
            if not conn_manager.register(conn):
                print(f"[!] Duplicate connection from {addr[0]}:{addr[1]} - closing")
                conn.close()
        elif event_type == "error":
            print(f"[!] Server error: {err}")

    return handle_accept


def establish_connections(targets: List[Tuple], conn_manager: ConnectionManager, msg_handler):
    """Establish outgoing connections to specified peers"""
    for target in targets:
        try:
            client_conn = Client(target, msg_handler)
            if conn_manager.register(client_conn):
                print(f"[+] Connected to {target[0]}:{target[1]}")
            else:
                print(f"[!] Already connected to {target[0]}:{target[1]}")
                client_conn.close()
        except Exception as err:
            print(f"[-] Cannot connect to {target[0]}:{target[1]} - {type(err).__name__}")


def main():
    listen_port, initial_peers = validate_cli_args()

    conn_manager = ConnectionManager()
    msg_handler = build_message_handler(conn_manager)
    accept_handler = build_accept_handler(conn_manager, msg_handler)

    nickname = input("Your nickname: ").strip()
    while not nickname:
        nickname = input("Please enter a valid nickname: ").strip()

    server_instance = Server(listen_port, accept_handler)

    if initial_peers:
        print(f"\n[*] Connecting to {len(initial_peers)} peer(s)...")
        establish_connections(initial_peers, conn_manager, msg_handler)

    print(f"\n[*] Ready! You are '{nickname}'")
    print("[*] Type messages and press ENTER to broadcast")
    print("[*] Press CTRL+C to quit\n")

    try:
        while True:
            msg_text = input()
            distribute_message(msg_text, nickname, conn_manager)
    except (EOFError, KeyboardInterrupt):
        print("\n\n[*] Shutting down...")
    finally:
        conn_manager.shutdown()
        server_instance.close()
        print("[*] Bye!")


if __name__ == "__main__":
    main()