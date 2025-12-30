from snippets.lab3 import *
import sys
import uuid
import threading


EXIT_MESSAGE = "<LEAVES THE CHAT>"
SEEN_MAX = 2000

# set per salvataggio connessione
connections = set()
# evitare problemi nei thread
conn_locck = threading.Lock()

# set di peer
seen = set()
# evitare problmi tra thread
seen_lock = threading.Lock()


def remember(msg_id: str) -> bool:
    """
    True  => già visto e quindi si scarta
    False => nuovo e quindi si tiene
    """
    with seen_lock:
        if msg_id in seen:
            return True
        seen.add(msg_id)
        if len(seen) > SEEN_MAX:
            seen.clear()
        return False


def add_connection(conn: Connection):
    """
    aggiunta connessione e callback
    """
    with conn_locck:
        connections.add(conn)
    conn.callback = on_message_received
    print(f"Connected with peer: {conn.remote_address}")


def remove_connection(conn: Connection):
    """
    rimozione connessione
    """
    with conn_locck:
        connections.discard(conn)


def broadcast(raw: str, exclude: Connection | None = None):
    """
    invio a tutti i peer rilevati
    """
    with conn_locck:
        conns = [c for c in connections if not c.closed]

    for c in conns:
        if exclude is not None and c is exclude:
            continue
        try:
            c.send(raw)
        except Exception:
            try:
                c.close()
            finally:
                remove_connection(c)


def send_message(msg, sender):
    """invio messaggio
    """
    msg = (msg or "").strip()
    if not msg:
        print("Empty message, not sent")
        return

    payload = message(msg, sender)
    raw = f"{uuid.uuid4().hex}|{payload}"

    print(payload)

    broadcast(raw)


def on_message_received(event, payload, connection, error):
    """
    callback ricezione messaggi
    """
    match event:
        case "message":
            if not payload:
                return
                        
            # se il payload non è quello atteso
            if '|' not in payload:
                msg_id, real_payload = None, payload
            else:
                msg_id, real_payload = payload.split('|', 1)

            if msg_id is None:
                print(real_payload)
                return

            # verifico se ho già visto il mesg
            if remember(msg_id):
                return

            print(real_payload)

            # forward agli altri (gruppo)
            broadcast(payload, exclude=connection)

        case "close":
            print(f"Connection with peer {connection.remote_address} closed")
            remove_connection(connection)

        case "error":
            print(error)
            remove_connection(connection)


def on_new_connection(event, connection, address, error):
    match event:
        case "listen":
            print(f"Peer listening on port {address[1]} at {', '.join(local_ips())}")
        case "connect":
            print(f"Incoming connection from: {address}")
            add_connection(connection)
        case "stop":
            print("Stop listening for new connections")
        case "error":
            print(error)


port = int(sys.argv[1])
peers = [address(p) for p in sys.argv[2:]]

server = Server(port, on_new_connection)

# connessioni in uscita
for ep in peers:
    try:
        c = Client(ep)
        # salvataggio connessione e set della callback
        add_connection(c)
    except Exception:
        pass

print(f"Bound to: {('0.0.0.0', port)}")
print(f"Local IP addresses: {list(local_ips())}")

username = input("Enter your username to start the chat:\n")
print("Type your message and press Enter to send it. Messages from other peers will be displayed below.")

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        send_message(EXIT_MESSAGE, username)
        break


for c in connections:
    try:
        c.close()
    except Exception:
        pass
server.close()
