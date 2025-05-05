import socket
import threading
import sys

BUFFER_SIZE = 1024

# Funzioni per il Server
def start_server(host, port):
    clients = {}

    def broadcast(message, sender=""):
        """Invia un messaggio a tutti i client connessi."""
        for client in clients:
            try:
                client.sendall(bytes(sender, "utf8") + message)
            except Exception as e:
                print(f"Errore durante l'invio al client: {e}")

    def handle_client(client_socket):
        """Gestisce un singolo client."""
        try:
            name = client_socket.recv(BUFFER_SIZE).decode("utf8")
            if not name:
                raise ConnectionError("Nome non ricevuto.")

            welcome_message = f"Benvenuto {name}! Scrivi {{exit}} per uscire dalla chat."
            client_socket.sendall(bytes(welcome_message, "utf8"))
            broadcast(bytes(f"{name} si è unito alla chat.\n", "utf8"))
            clients[client_socket] = name

            while True:
                message = client_socket.recv(BUFFER_SIZE)
                if message == bytes("{exit}", "utf8"):
                    broadcast(bytes(f"{name} ha lasciato la chat.\n", "utf8"))
                    break
                else:
                    broadcast(message, f"{name}: ")

        except Exception as e:
            print(f"Errore con il client: {e}")
        finally:
            client_socket.close()
            clients.pop(client_socket, None)

    # Setup server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server avviato su {host}:{port}")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Connessione da {client_address}")
            threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
        except KeyboardInterrupt:
            print("Server in chiusura...")
            break
        except Exception as e:
            print(f"Errore server: {e}")

    server_socket.close()

# Funzioni per il Client
def start_client(host, port):
    def receive_messages(sock):
        """Riceve messaggi dal server e li mostra."""
        while True:
            try:
                message = sock.recv(BUFFER_SIZE).decode("utf8")
                if not message:
                    break
                print(message)
            except Exception:
                print("Connessione al server persa.")
                break

    def send_messages(sock):
        """Invia messaggi al server."""
        try:
            username = input("Inserisci il tuo nome: ").strip()
            sock.sendall(bytes(username, "utf8"))

            while True:
                message = input()
                sock.sendall(bytes(message, "utf8"))
                if message == "{exit}":
                    print("Disconnessione...")
                    break
        except Exception as e:
            print(f"Errore di invio: {e}")
        finally:
            sock.close()

    # Setup client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print(f"Connesso al server su {host}:{port}")

        # Avvio dei thread per ricezione e invio messaggi
        threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
        send_messages(client_socket)

    except Exception as e:
        print(f"Errore di connessione: {e}")
    finally:
        client_socket.close()

# Entry point
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python exercise_tcp_group_chat.py <server|client> <HOST> <PORT>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    host = sys.argv[2]
    port = int(sys.argv[3])

    if mode == "server":
        start_server(host, port)
    elif mode == "client":
        start_client(host, port)
    else:
        print("Modalità non valida. Usa 'server' o 'client'.")
        sys.exit(1)
