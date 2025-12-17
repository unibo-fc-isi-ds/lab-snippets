from snippets.lab3 import *
import sys

remote_peers = set()


def broadcast(msg, sender):
    """Send the formatted message to all active peers."""
    text = msg.strip()
    if not text:
        return
    for peer in list(remote_peers):
        try:
            peer.send(message(text, sender))
        except Exception as e:
            print(f"[WARN] send failed to {peer.remote_address}: {e}")
            remote_peers.discard(peer)


def on_message_received(event, payload, connection, error):
    match event:
        case "message":
            print(payload)
        case "close":
            remote_peers.discard(connection)
            print(f"Connection closed with {connection.remote_address}")
        case "error":
            print(f"[ERROR] {error}")


def on_new_connection(event, connection, address, error):
    match event:
        case "listen":
            print(f"Server listening on port {address[1]} at {', '.join(local_ips())}")
        case "connect":
            connection.callback = on_message_received
            remote_peers.add(connection)
            print(f"Incoming connection from {address}")
        case "stop":
            print("Stop listening")
        case "error":
            print(f"[ERROR] {error}")


def connect_to_peers(endpoints):
    for ep in endpoints:
        try:
            peer = Client(address(ep), on_message_received)
            remote_peers.add(peer)
            print(f"Connected to {peer.remote_address}")
        except Exception as e:
            print(f"[WARN] not connected to {ep}: {e}")


def parse_args(argv):
    if not argv:
        raise SystemExit("Usage: python exercise_tcp_group_chat.py PORT [PEER1 PEER2 ...]")
    try:
        port = int(argv[0])
    except ValueError:
        raise SystemExit("Port must be an integer")
    peers_list = argv[1:]
    return port, peers_list


listen_port, peers_list = parse_args(sys.argv[1:])

server = Server(listen_port, on_new_connection)
connect_to_peers(peers_list)

username = input("Username: ")
print("Type and press Enter to send. Ctrl+C or EOF to quit.")
try:
    for line in sys.stdin:
        broadcast(line, username)
except KeyboardInterrupt:
    pass
finally:
    for p in list(remote_peers):
        p.close()
    server.close()
