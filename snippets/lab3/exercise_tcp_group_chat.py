import argparse
import socket
import threading
import sys


# ----------------- GESTIONE PEER -----------------

peers = set()          # insieme di socket aperti verso altri peer
peers_lock = threading.Lock()


def add_peer(sock: socket.socket):
    """Aggiunge un peer alla lista condivisa."""
    with peers_lock:
        peers.add(sock)


def remove_peer(sock: socket.socket):
    """Rimuove un peer (e chiude il socket)."""
    with peers_lock:
        if sock in peers:
            peers.remove(sock)
    try:
        sock.close()
    except OSError:
        pass


def broadcast(msg: str):
    """Invia il messaggio a tutti i peer conosciuti."""
    if not msg:
        return
    data = (msg + "\n").encode("utf-8")
    with peers_lock:
        current_peers = list(peers)
    for s in current_peers:
        try:
            s.sendall(data)
        except OSError:
            # se il peer non risponde più, lo eliminiamo
            remove_peer(s)


# ----------------- THREAD DI RICEZIONE -----------------

def recv_loop(sock: socket.socket, addr):
    """Riceve messaggi da UN singolo peer e li stampa a schermo."""
    add_peer(sock)
    buffer = b""
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                text = line.decode("utf-8", errors="replace")
                # stampa messaggi ricevuti
                print(f"[{addr[0]}:{addr[1]}] {text}")
    except OSError:
        pass
    finally:
        remove_peer(sock)


# ----------------- THREAD SERVER (ACCEPT) -----------------

def accept_loop(listen_sock: socket.socket):
    """Accetta nuove connessioni in ingresso e crea un thread per ognuna."""
    while True:
        try:
            conn, addr = listen_sock.accept()
        except OSError:
            # socket di ascolto chiuso -> usciamo
            break
        t = threading.Thread(target=recv_loop, args=(conn, addr), daemon=True)
        t.start()


# ----------------- CONNESSIONE AI PEER ESISTENTI -----------------

def connect_to_peer(host: str, port: int):
    """Crea una connessione TCP verso un altro peer e avvia il thread di ricezione."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
    except OSError as e:
        print(f"Impossibile connettersi a {host}:{port}: {e}")
        return
    # una volta connessi, lanciamo il thread che ascolta da questo peer
    addr = s.getpeername()
    t = threading.Thread(target=recv_loop, args=(s, addr), daemon=True)
    t.start()


# ----------------- MAIN -----------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="TCP Group Chat peer (ogni processo è server e client)"
    )
    parser.add_argument(
        "--port", type=int, required=True,
        help="porta TCP locale su cui mettersi in ascolto"
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="indirizzo locale di ascolto (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--peers", nargs="*", default=[],
        help="lista di peer da contattare all'avvio, formato host:port"
    )
    return parser.parse_args(argv)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    # 1. Creazione socket di ascolto
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((args.host, args.port))
    listen_sock.listen()
    print(f"[INFO] In ascolto su {args.host}:{args.port}")

    # 2. Thread che accetta connessioni in ingresso
    accept_thread = threading.Thread(
        target=accept_loop, args=(listen_sock,), daemon=True
    )
    accept_thread.start()

    # 3. Connessione ai peer passati da riga di comando
    for peer_str in args.peers:
        try:
            host, port_str = peer_str.split(":")
            port = int(port_str)
        except ValueError:
            print(f"[WARN] Peer non valido (uso host:port): {peer_str}")
            continue
        connect_to_peer(host, port)

    # 4. Loop principale: leggi da tastiera e broadcast
    username = input("Inserisci il tuo username per la chat:\n")
    print("Scrivi un messaggio e premi Invio per inviarlo. "
          "Ctrl+C per uscire.\n")

    try:
        while True:
            try:
                content = input()
            except EOFError:
                break
            msg = f"{username}: {content}"
            broadcast(msg)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[INFO] Chiusura in corso...")
        # chiudiamo il socket di ascolto -> termina accept_loop
        try:
            listen_sock.close()
        except OSError:
            pass
        # chiudiamo tutti i peer
        with peers_lock:
            current_peers = list(peers)
        for s in current_peers:
            remove_peer(s)


if __name__ == "__main__":
    main()