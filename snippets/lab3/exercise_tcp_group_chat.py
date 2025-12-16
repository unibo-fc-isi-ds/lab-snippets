from snippets.lab3 import *
import sys

remote_peers = set()


def broadcast(msg, sender):
    """Invia il messaggio formattato a tutti i peer attivi."""
    text = msg.strip()
    if not text:
        return
    for peer in list(remote_peers):
        try:
            peer.send(message(text, sender))
        except Exception as e:
            print(f"[WARN] invio fallito verso {peer.remote_address}: {e}")
            remote_peers.discard(peer)


def on_message_received(event, payload, connection, error):
    match event:
        case "message":
            print(payload)
        case "close":
            remote_peers.discard(connection)
            print(f"Connessione chiusa con {connection.remote_address}")
        case "error":
            print(f"[ERR] {error}")


def on_new_connection(event, connection, address, error):
    match event:
        case "listen":
            print(f"Server in ascolto sulla porta {address[1]} su {', '.join(local_ips())}")
        case "connect":
            connection.callback = on_message_received
            remote_peers.add(connection)
            print(f"Connessione in ingresso da {address}")
        case "stop":
            print("Stop ascolto")
        case "error":
            print(f"[ERR] {error}")


def connect_to_peers(endpoints):
    for ep in endpoints:
        try:
            peer = Client(address(ep), on_message_received)
            remote_peers.add(peer)
            print(f"Connesso a {peer.remote_address}")
        except Exception as e:
            print(f"[WARN] non connesso a {ep}: {e}")


def parse_args(argv):
    if not argv:
        raise SystemExit("Uso: python exercise_tcp_group_chat.py PORT [PEER1 PEER2 ...]")
    try:
        port = int(argv[0])
    except ValueError:
        raise SystemExit("La porta deve essere un intero")
    peers_list = argv[1:]
    return port, peers_list


if __name__ == "__main__":
    listen_port, peers_list = parse_args(sys.argv[1:])

    server = Server(listen_port, on_new_connection)
    connect_to_peers(peers_list)

    username = input("Username: ")
    print("Scrivi e premi Invio per inviare. Ctrl+C o EOF per uscire.")
    try:
        for line in sys.stdin:
            broadcast(line, username)
    except KeyboardInterrupt:
        pass
    finally:
        for p in list(remote_peers):
            p.close()
        server.close()
