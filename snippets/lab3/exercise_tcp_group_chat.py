"""
TCP Group Chat (exercise - lab3)

Run:
    python -m snippets.lab3.exercise_tcp_group_chat <listen_port> [peer_ip:peer_port ...]
Example (3 terminals):
    # Terminal A
    python -m snippets.lab3.exercise_tcp_group_chat 9001
    # Terminal B
    python -m snippets.lab3.exercise_tcp_group_chat 9002 127.0.0.1:9001
    # Terminal C
    python -m snippets.lab3.exercise_tcp_group_chat 9003 127.0.0.1:9001

Notes:
- No strict client/server distinction: every peer listens for incoming TCP connections
  and also actively connects to known peers.
- Peers can join/leave at any time.
- Messages are gossiped over the overlay: a peer forwards each chat message to all
  currently connected peers (except the one it arrived from). A message id prevents loops.
"""

from __future__ import annotations

from snippets.lab3 import Server, Client, Connection, address, message, local_ips
import json
import sys
import threading
import uuid
from typing import Dict, Optional, Set, Tuple, List


Endpoint = Tuple[str, int]


def ep_to_str(ep: Endpoint) -> str:
    return f"{ep[0]}:{ep[1]}"


def str_to_ep(s: str) -> Endpoint:
    host, port = s.rsplit(":", 1)
    return host, int(port)


class TcpGroupChatPeer:
    """
    A single peer that:
      - listens on TCP <listen_port>
      - keeps connections to other peers
      - exchanges HELLO messages to learn each other's listening endpoints
      - forwards ("gossips") chat messages to all known connections
    """

    def __init__(self, listen_port: int, seed_peers: List[Endpoint], username: str):
        self.username = username
        self.listen_port = listen_port

        # Bind on all interfaces, but ADVERTISE a concrete, connectable IP.
        self.bind_ep: Endpoint = ("0.0.0.0", listen_port)
        self.advertise_ip: str = self.pick_advertise_ip()
        self.listen_ep: Endpoint = (self.advertise_ip, listen_port)

        self._server = Server(listen_port, self.on_new_connection)

        # Shared state (accessed from multiple receiver threads)
        self._lock = threading.RLock()
        self._by_endpoint: Dict[Endpoint, Connection] = {}  # remote listening endpoint -> connection
        self._by_conn: Dict[Connection, Endpoint] = {}      # connection -> remote listening endpoint (after HELLO)
        self._known_endpoints: Set[Endpoint] = set(seed_peers)
        self._seen_messages: Set[str] = set()

        # Try connecting to seeds (best effort)
        for ep in list(seed_peers):
            self.connect_to(ep)

        print(f"Listening on {self.listen_ep[1]} (advertise {self.listen_ep[0]}) at {', '.join(local_ips())}")

    def pick_advertise_ip(self) -> str:
        ips = list(local_ips())
        # Prefer a non-loopback address if available (useful on a LAN).
        for ip in ips:
            if not ip.startswith("127."):
                return ip
        # Fallback to localhost for single-machine tests.
        return ips[0] if ips else "127.0.0.1"

    # networking helpers

    def send_json(self, conn: Connection, obj: dict) -> None:
        conn.send(json.dumps(obj, separators=(",", ":")))

    def broadcast_json(self, obj: dict, except_conn: Optional[Connection] = None) -> None:
        with self._lock:
            conns = list(self._by_endpoint.values())
        for c in conns:
            if except_conn is not None and c is except_conn:
                continue
            try:
                self.send_json(c, obj)
            except Exception:
                pass

    def connect_to(self, ep: Endpoint) -> None:
        """Connect to ep (remote listening endpoint) if not already connected."""
        with self._lock:
            if ep in self._by_endpoint:
                return
            if ep == self.listen_ep:
                return
            self._known_endpoints.add(ep)

        try:
            conn = Client(ep, self.on_message_received)
        except Exception:
            return

        hello = {
            "type": "hello",
            "listen": ep_to_str(self.listen_ep),
            "name": self.username,
            "peers": [ep_to_str(p) for p in self.snapshot_known_peers()],
        }
        try:
            self.send_json(conn, hello)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return

        # store temporarily using TCP peer address until HELLO maps the real listen endpoint
        with self._lock:
            tmp_ep = conn.remote_address
            if tmp_ep not in self._by_endpoint:
                self._by_endpoint[tmp_ep] = conn

    def snapshot_known_peers(self) -> Set[Endpoint]:
        with self._lock:
            s = set(self._known_endpoints)
            s.add(self.listen_ep)
            s |= set(self._by_endpoint.keys())
        return {ep for ep in s if isinstance(ep[1], int) and 0 <= ep[1] <= 65535}

    # event handlers

    def on_new_connection(self, event, connection: Connection, address: Endpoint, error):
        if event == "connect":
            connection.callback = self.on_message_received
            with self._lock:
                if address not in self._by_endpoint:
                    self._by_endpoint[address] = connection
        else:
            return


    def on_message_received(self, event, payload, connection: Connection, error):
        if event == "error":
            return

        if event == "close":
            with self._lock:
                ep = self._by_conn.pop(connection, None)
                to_del = [k for k, v in self._by_endpoint.items() if v is connection]
                for k in to_del:
                    self._by_endpoint.pop(k, None)
                if ep is not None:
                    self._known_endpoints.add(ep)
            return

        if event != "message" or not payload:
            return

        try:
            obj = json.loads(payload)
        except Exception:
            return

        t = obj.get("type")
        if t == "hello":
            self.handle_hello(obj, connection)
        elif t == "chat":
            self.handle_chat(obj, connection)

    def handle_hello(self, obj: dict, connection: Connection) -> None:
        try:
            remote_listen = str_to_ep(obj["listen"])
        except Exception:
            return

        with self._lock:
            # remove placeholder keys for this connection
            for k, v in list(self._by_endpoint.items()):
                if v is connection and k != remote_listen:
                    self._by_endpoint.pop(k, None)

            # avoid duplicates
            if remote_listen in self._by_endpoint and self._by_endpoint[remote_listen] is not connection:
                try:
                    connection.close()
                except Exception:
                    pass
                return

            self._by_endpoint[remote_listen] = connection
            self._by_conn[connection] = remote_listen
            self._known_endpoints.add(remote_listen)

        # reply with our HELLO
        reply = {
            "type": "hello",
            "listen": ep_to_str(self.listen_ep),
            "name": self.username,
            "peers": [ep_to_str(p) for p in self.snapshot_known_peers()],
        }
        try:
            self.send_json(connection, reply)
        except Exception:
            return

        # connect to newly discovered peers
        peers = obj.get("peers") or []
        for p in peers:
            try:
                ep = str_to_ep(p)
            except Exception:
                continue
            if ep == self.listen_ep:
                continue
            with self._lock:
                self._known_endpoints.add(ep)
                already = ep in self._by_endpoint
            if not already:
                self.connect_to(ep)

    def handle_chat(self, obj: dict, connection: Connection) -> None:
        msg_id = obj.get("id")
        sender = obj.get("from", "unknown")
        text = obj.get("text", "")

        if not msg_id or not isinstance(msg_id, str):
            return

        with self._lock:
            if msg_id in self._seen_messages:
                return
            self._seen_messages.add(msg_id)
            if len(self._seen_messages) > 5000:
                self._seen_messages = set(list(self._seen_messages)[-2500:])

        if text:
            print(message(text, sender))

        self.broadcast_json(obj, except_conn=connection)

    # user interaction

    def send_user_message(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return

        obj = {
            "type": "chat",
            "id": uuid.uuid4().hex,
            "from": self.username,
            "text": text,
        }

        with self._lock:
            self._seen_messages.add(obj["id"])

        self.broadcast_json(obj, except_conn=None)

    def close(self) -> None:
        try:
            self._server.close()
        except Exception:
            pass
        with self._lock:
            for c in list(self._by_endpoint.values()):
                try:
                    c.close()
                except Exception:
                    pass
            self._by_endpoint.clear()
            self._by_conn.clear()


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python -m snippets.lab3.exercise_tcp_group_chat <listen_port> [peer_ip:peer_port ...]")
        return 2

    listen_port = int(argv[1])
    seed_peers: List[Endpoint] = []
    for s in argv[2:]:
        try:
            seed_peers.append(address(s))
        except Exception:
            print(f"Invalid peer endpoint: {s}")
            return 2

    username = input("Enter your username to start the chat:\n").strip() or "anonymous"
    print(
        "Type your message and press Enter to send it. Messages from other peers will be displayed below.\n"
        "(Ctrl+C to quit)"
    )

    peer = TcpGroupChatPeer(listen_port, seed_peers, username)
    try:
        while True:
            try:
                line = input()
            except EOFError:
                break
            peer.send_user_message(line)
    except KeyboardInterrupt:
        pass
    finally:
        peer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
