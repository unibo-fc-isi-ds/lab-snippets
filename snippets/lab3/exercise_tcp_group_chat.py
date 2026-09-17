"""
Usage:
    poetry run python -u -m snippets.lab3.exercise_tcp_group_chat 9001
    poetry run python -u -m snippets.lab3.exercise_tcp_group_chat 9002 127.0.0.1:9001
    poetry run python -u -m snippets.lab3.exercise_tcp_group_chat 9003 127.0.0.1:9001 127.0.0.1:9002
    shutdown on Ctrl+C or /quit.
"""

from snippets.lab3 import *
import sys
import threading
import signal
import json
from datetime import datetime
from uuid import uuid4

class GroupPeer:
    def __init__(self, listen_port: int, initial_peers=None):
        if initial_peers is None:
            initial_peers = []
        self.listen_port = int(listen_port)
        self.server = Server(self.listen_port, callback=self._on_server_event)
        self._conns = {}
        self._lock = threading.Lock()
        self.sender_id = str(uuid4()) # unique id for this peer
        self.my_username = None # will be set later by user
        for host, port in initial_peers:
            t = threading.Thread(target=self._connect_to, args=(host, port), daemon=True)
            t.start()

    def _on_server_event(self, event: str, connection: Connection = None, address: tuple = None, error: Exception = None):
        match event:
            case 'listen':
                addr = address
                print(f"[INFO] Server listening on {addr[0]}:{addr[1]} (local IPs: {', '.join(local_ips())})", flush=True)
            case 'connect':
                print(f"[INFO] Incoming connection from {address}", flush=True)
                connection.callback = self._on_connection_event
                self._register_connection(connection)
            case 'stop':
                print("[INFO] Server stopped listening", flush=True)
            case 'error':
                print("[ERROR] Server error:", error, flush=True)

    def _connect_to(self, host, port):
        try:
            conn = Client(address(f"{host}:{port}"), callback=self._on_connection_event)
            print(f"[OUT] Connected (outgoing) to {conn.remote_address}", flush=True)
            self._register_connection(conn)
        except Exception as e:
            print(f"[ERROR] outgoing connection to {(host, port)} failed: {e}", flush=True)

    def _register_connection(self, conn: Connection):
        with self._lock:
            self._conns[id(conn)] = conn

    def _unregister_connection(self, conn: Connection):
        with self._lock:
            self._conns.pop(id(conn), None)

    def _on_connection_event(self, event: str, payload: str = None, connection: Connection = None, error: Exception = None):
        match event:
            case 'message':
                self._register_connection(connection) # remember the connection if its incoming
                try:
                    parsed = json.loads(payload)
                except Exception:
                    print(payload, flush=True)
                    return
                if isinstance(parsed, dict) and parsed.get("type") == "chat":
                    sid = parsed.get("sender_id") # if sender_id matches then show "You"
                    if sid is not None and sid == self.sender_id:
                        formatted_you = parsed.get("formatted_you")
                        if formatted_you:
                            print(formatted_you, flush=True)
                        else:
                            ts = parsed.get("timestamp", "<no-ts>")
                            text = parsed.get("text", "")
                            print(f"[{ts}] You:\n\t{text}", flush=True)
                    else:
                        formatted = parsed.get("formatted")
                        if formatted:
                            print(formatted, flush=True)
                        else:
                            ts = parsed.get("timestamp", "<no-ts>")
                            sender = parsed.get("sender", "<unknown>")
                            text = parsed.get("text", "")
                            print(f"[{ts}] {sender}:\n\t{text}", flush=True)
                else:
                    print(payload, flush=True)
            case 'close':
                try:
                    remote = connection.remote_address
                except Exception:
                    remote = None
                print(f"[INFO] Connection closed by remote {remote}", flush=True)
                self._unregister_connection(connection)
            case 'error':
                print("[ERROR] connection error:", error, flush=True)
                self._unregister_connection(connection)

    def send_all(self, text: str, sender: str):
        ts = datetime.now()
        formatted = message(text, sender, ts) # e.g. "[2025-12-08T14:00:00] Heisenberg:\n\tHello"
        formatted_you = f"[{ts.isoformat()}] You:\n\t{text}" #just shows "You" as sender
        obj = {
            "type": "chat",
            "sender": sender,
            "sender_id": self.sender_id,
            "text": text,
            "timestamp": ts.isoformat(),
            "formatted": formatted,
            "formatted_you": formatted_you
        }
        payload = json.dumps(obj)
        with self._lock:
            conns = list(self._conns.values())
        print(formatted_you, flush=True)
        if not conns:
            print("[WARN] No peers connected, message not sent to anyone.", flush=True)
            return
        for c in conns:
            try:
                c.send(payload)
            except Exception as e:
                print(f"[ERROR] failed to send to {getattr(c, 'remote_address', None)}: {e}", flush=True)

    def list_peers(self):
        with self._lock:
            return [getattr(c, 'remote_address', None) for c in self._conns.values()]

    def close(self):
        try:
            self.server.close()
        except:
            pass
        with self._lock:
            conns = list(self._conns.values())
            self._conns.clear()
        for c in conns:
            try:
                c.close()
            except:
                pass
        print("[INFO] Peer shutdown", flush=True)


def parse_address(arg: str):
    return address(arg)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 exercise_tcp_group_chat.py <listen_port> [peer1_ip:peer1_port ...]", flush=True)
        sys.exit(1)

    listen = int(sys.argv[1])
    initial_peers = [parse_address(p) for p in sys.argv[2:]]
    peer = GroupPeer(listen, initial_peers)

    username = input("Enter your username to start the chat:\n")
    peer.my_username = username
    print("Type your message and press Enter to send it. Commands: /peers  /quit", flush=True)

    _shutdown = threading.Event()

    def _sigint(signum, frame):
        # run shutdown exactly once
        if _shutdown.is_set():
            print("[INFO] already shutting down...", flush=True)
            return
        _shutdown.set()
        print("\n[INFO] exiting...", flush=True)
        try:
            peer.close()
        except Exception:
            pass

    signal.signal(signal.SIGINT, _sigint)

    try:
        while not _shutdown.is_set():
            try:
                line = input()
            except KeyboardInterrupt:
                # Ctrl+C to shutdown
                _sigint(None, None)
                break
            except EOFError:
                break
            if not line:
                continue
            cmd = line.strip()
            if cmd == "/peers":
                print("Known peers:", peer.list_peers(), flush=True)
                continue
            if cmd in ("/quit", "/exit"):
                _shutdown.set()
                break
            peer.send_all(line, username)
    finally:
        if not _shutdown.is_set():
            _shutdown.set()
        try:
            peer.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
