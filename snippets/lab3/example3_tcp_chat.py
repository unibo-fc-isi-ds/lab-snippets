from snippets.lab3 import *
import sys

mode = sys.argv[1].lower().strip()
remote_peers = []  # Lista dei peer connessi (solo lato server)


def send_message(msg, sender):
    """Invia un messaggio a tutti i peer connessi."""
    if not remote_peers:
        print("Nessun peer connesso, il messaggio è perso")
    elif msg.strip():
        for peer in remote_peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Messaggio vuoto, non inviato")


def on_message_received(event, payload, connection, error):
    """Gestisce i messaggi ricevuti e altri eventi."""
    match event:
        case 'message':
            print(payload)  
            if mode == 'server':
                for peer in remote_peers:
                    if peer != connection:  
                        peer.send(payload)
        case 'close':
            print(f"Connessione con il peer {connection.remote_address} chiusa")
            if mode == 'server' and connection in remote_peers:
                remote_peers.remove(connection)
        case 'error':
            print(f"Errore: {error}")


if mode == 'server':
    port = int(sys.argv[2])

    def on_new_connection(event, connection, address, error):
        """Gestisce nuove connessioni in ingresso."""
        match event:
            case 'listen':
                print(f"Server in ascolto sulla porta {port} all'indirizzo {', '.join(local_ips())}")
            case 'connect':
                print(f"Nuova connessione da: {address}")
                connection.callback = on_message_received
                remote_peers.append(connection) 
            case 'stop':
                print("Interrotto l'ascolto per nuove connessioni")
            case 'error':
                print(f"Errore: {error}")

    server = Server(port, on_new_connection)

elif mode == 'client':
    remote_endpoint = sys.argv[2]
    remote_peer = Client(address(remote_endpoint), on_message_received)
    remote_peers.append(remote_peer)  
    print(f"Connesso al server {remote_peer.remote_address}")


username = input("Inserisci il tuo username per iniziare la chat:\n")
print("Scrivi il messaggio e premi Invio per inviarlo. I messaggi degli altri peer verranno mostrati qui.")

try:
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    print("Disconnessione in corso...")
    for peer in remote_peers:
        peer.close()  
    if mode == 'server':
        server.close()
