# snippets/lab3/exercise_tcp_group_chat.py

from __future__ import annotations

from snippets.lab3 import *
import sys
import time

# Connessioni attive [Indirizzo, porta -> Client]
active_peers: dict[tuple[str, int], Client] = {}

# Storico dei peer con cui si è stati in contatto finora (anche non attivi ora)
#[Indirizzo, porta] solo per tener traccia di chi è stato contattato
known_peers: set[tuple[str, int]] = set()

shutting_down = False  #Per chiusura pulita


#Funzion per la gestione delle connessioni attive e conosciute
def add_active_peer(conn: Client) -> None:
    active_peers[conn.remote_address] = conn
    known_peers.add(conn.remote_address)

#Funzione per rimuovere connessioni attive
def remove_active_peer(conn: Client) -> None:
    active_peers.pop(conn.remote_address, None)


#Broadcast solo ai peer attivi:i peer non attivi vengono segnati come già contattati (known_peers) ma non ricevono nulla; 
#Il messaggio è creato con message(msg, sender) e inviato via conn.send().
def broadcast(msg: str, sender: str) -> None:
    if shutting_down:
        return
    msg = msg.strip()
    if not msg:
        print("Empty message, not sent")
        return

    # Se non ho peer attivi, la consegna fallisce (ma lo storico rimane)
    if not active_peers:
        print("No active peers connected, message is lost.")
        return
    
    #Richiamo funzione message 
    payload = message(msg, sender) 
    #Tengo traccia in questa lista dei peer a cui non sono riuscito a inviare il messaggio
    dead: list[tuple[str, int]] = []

    for addr, conn in list(active_peers.items()):
        try:
            conn.send(payload) 
        except Exception as e:
            print(f"Send failed to {addr}: {e}")
            dead.append(addr)

    # Pulizia delle connessioni morte
    for addr in dead:
        try:
            active_peers[addr].close()
        except Exception:
            pass
        active_peers.pop(addr, None)


#Callback che gestisce eventi: alla chiusura (close) rimuove il peer da active ma lo mantiene in known.
def on_message_received(event, payload, connection, error) -> None:
    global shutting_down
    if shutting_down:
        return
    match event:
        case "message":
            print(payload)
        case "close":
            print(f"Connection with peer {connection.remote_address} closed")
            remove_active_peer(connection) 
        case "error":
            print(error)


#Callback per nuove connessioni: quando una connessione arriva, le assegno le callback e la registra sia in active sia in known
def on_new_connection(event, connection, address, error) -> None:
    global shutting_down
    if shutting_down:
        try:
            connection.close()
        except Exception:
            pass
        return
    match event:
        case "listen":
            print(f"Peer listening on port {address[0]} at {', '.join(local_ips())}")
        case "connect":
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received  # [PROF]
            add_active_peer(connection)               # [NOI]
        case "stop":
            print("Stop listening for new connections")
        case "error":
            print(error)


#Parsing minimale degli argomenti: supporto join multipli leggendo tutti gli ip:port dopo --join.
def parse_join_args(argv: list[str]) -> list[str]:
    if "--join" not in argv:
        return []
    i = argv.index("--join")
    return [a for a in argv[i + 1 :] if not a.startswith("-")]

#Stampa semplice delle liste ordinate di peer attivi e conosciuti
def print_peers() -> None:
    active = sorted(active_peers.keys())
    known = sorted(known_peers)
    print("\n=== PEERS ===")
    print(f"Active ({len(active)}): {active}")
    print(f"Known  ({len(known)}): {known}")


#main
def main() -> None:
    if len(sys.argv) < 2:
        print("Python exercise_tcp_group_chat.py <port> [--join ip:port ip:port ...]")
        sys.exit(1)

    port = int(sys.argv[1])
    join_endpoints = parse_join_args(sys.argv)

    #Avvio server: ogni peer è anche server
    server = Server(port, on_new_connection)

    #Connessioni in uscita verso peer iniziali (peer è anche client)
    for ep in join_endpoints:
        try:
            c = Client(address(ep), on_message_received)
            add_active_peer(c)                           
            print(f"Connected to {c.remote_address}")
        except Exception as e:
            print(f"Failed connecting to {ep}: {e}")

    username = input("Enter your username to start the chat:\n")
    print("Type your message and press Enter to send it.")
    print("Commands: /peers to show active+known peers, /quit to exit.")

    try:
        while True:
            content = input()
            if content.strip() == "/quit":
                break
            if content.strip() == "/peers":
                print_peers()
                continue
            broadcast(content, username)
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        global shutting_down
        shutting_down = True
        for _, c in list(active_peers.items()):
            try:
                c.close()
            except Exception:
                pass
        active_peers.clear()
        try:
            server.close()      
        except Exception:
            pass

        time.sleep(0.2) 

if __name__ == "__main__":
    main()
