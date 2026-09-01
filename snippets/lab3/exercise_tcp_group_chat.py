import socket
import threading
import sys
import time
from datetime import datetime
import hashlib

###############################################################################
# Utility functions
###############################################################################

def parse_address(s: str):
    host, port = s.split(":")
    return (host, int(port))

def local_ips():
    result = []
    hostname = socket.gethostname()
    try:
        result.append(socket.gethostbyname(hostname))
    except:
        pass
    try:
        result.append(socket.gethostbyname("localhost"))
    except:
        pass
    return list(set(result))

def generate_msg_id(msg: str):
    """Generate a short hash for the message"""
    return hashlib.md5(msg.encode("utf-8")).hexdigest()

###############################################################################
# Connection class — handles one TCP connection with a peer
###############################################################################

class Connection:
    def __init__(self, sock: socket.socket, remote_addr, callback=None):
        self.sock = sock
        self.remote_addr = remote_addr
        self.callback = callback
        self.alive = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()

    def send(self, msg: str):
        try:
            data = (msg + "\n").encode("utf-8")
            with self.lock:
                self.sock.sendall(data)
        except Exception as e:
            self.alive = False
            if self.callback:
                self.callback("error", str(e), self, None)

    def close(self):
        if self.alive:
            self.alive = False
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.sock.close()
            except:
                pass
            if self.callback:
                self.callback("close", None, self, None)

    def _receive_loop(self):
        buffer = b""
        try:
            while self.alive:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    text = line.decode("utf-8", errors="ignore")
                    if self.callback:
                        self.callback("message", text, self, None)
        except Exception as e:
            if self.callback:
                self.callback("error", str(e), self, None)
        self.close()

###############################################################################
# Peer class — this is BOTH a server and a client
###############################################################################

class Peer:
    def __init__(self, listen_port, known_peers):
        self.listen_port = listen_port
        self.known_peers = known_peers
        self.connections = {}  # (ip,port) -> Connection
        self.running = True
        self.received_msg_ids = set()  # prevent message loops

        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()

        for addr in known_peers:
            self.connect_to_peer(addr)

    ############################################################################
    # SERVER SIDE
    ############################################################################
    def _server_loop(self):
        print(f"[SERVER] Listening on port {self.listen_port} at {', '.join(local_ips())}")
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("0.0.0.0", self.listen_port))
        srv.listen()
        while self.running:
            try:
                sock, addr = srv.accept()
                self._handle_new_connection(sock, addr)
            except:
                break

    def _handle_new_connection(self, sock, addr):
        print(f"[SERVER] Incoming connection from {addr}")
        conn = Connection(sock, addr, callback=self._on_message)
        self.connections[addr] = conn

    ############################################################################
    # CLIENT SIDE
    ############################################################################
    def connect_to_peer(self, addr):
        if addr in self.connections:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)
            print(f"[CLIENT] Connected to {addr}")
            conn = Connection(sock, addr, callback=self._on_message)
            self.connections[addr] = conn
        except Exception as e:
            print(f"[CLIENT] Could not connect to {addr}: {e}")

    ############################################################################
    # MESSAGE HANDLING
    ############################################################################
    def _on_message(self, event, payload, conn, error):
        if event == "message":
            msg_id = generate_msg_id(payload)
            if msg_id in self.received_msg_ids:
                return  # already processed
            self.received_msg_ids.add(msg_id)

            print(payload)

            # Broadcast message to all except the sender
            for peer_addr, peer_conn in list(self.connections.items()):
                if peer_conn is not conn:
                    peer_conn.send(payload)

        elif event == "close":
            print(f"[INFO] Peer {conn.remote_addr} disconnected")
            self.connections.pop(conn.remote_addr, None)

        elif event == "error":
            print(f"[ERROR] Connection {conn.remote_addr}: {error}")
            self.connections.pop(conn.remote_addr, None)

    ############################################################################
    # PUBLIC API
    ############################################################################
    def broadcast(self, msg: str):
        msg_id = generate_msg_id(msg)
        if msg_id in self.received_msg_ids:
            return
        self.received_msg_ids.add(msg_id)
        for conn in list(self.connections.values()):
            conn.send(msg)

###############################################################################
# MAIN — CLI interface
###############################################################################

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python exercise_tcp_group_chat.py PORT peer1:port peer2:port ...")
        sys.exit(1)

    listen_port = int(sys.argv[1])
    known = [parse_address(s) for s in sys.argv[2:]]

    peer = Peer(listen_port, known)

    username = input("Enter your username: ")

    print("Chat started. Type messages and press Enter.")
    print("Peers will receive them.")

    try:
        while True:
            text = input()
            timestamp = datetime.now().strftime("%H:%M:%S")
            msg = f"[{timestamp}] {username}: {text}"
            peer.broadcast(msg)

    except (KeyboardInterrupt, EOFError):
        print("Exiting...")


if __name__ == "__main__":
    main()
