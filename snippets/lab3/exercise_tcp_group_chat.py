import socket as s
import threading as th
import sys

bufferSize = 1024

##################################################################################Server functions
def server_func(host, port):
    addr = {}
    clients = {}

    def broadcast(message, sender=""):
        for client in list(clients):  #list(clients) is a copy of clients list, to avoid problems
            try:
                client.send(bytes(sender, "utf8") + message)
            except Exception:
                print(f"Connection lost with {clients[client]}. Removing client.")
                del clients[client]

    def handle_client(client):
        try:
            name = client.recv(bufferSize).decode("utf8")
            welcome_message = f"Welcome {name}! Type 'exit()' to leave the chat."
            client.send(bytes(welcome_message, "utf8"))
            broadcast(bytes(f"{name} joined the chat.", "utf8"), sender="Server: ")
            clients[client] = name

            while True:
                try:
                    message = client.recv(bufferSize).decode("utf8")
                    if not message or message.strip() == "exit()": 
                        leave_message = f"{name} has left the chat."
                        print(leave_message)  
                        broadcast(bytes(leave_message, "utf8"), sender="Server: ")
                        break
                    broadcast(bytes(message, "utf8"), f"{name}: ")
                except Exception:
                    break
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            if client in clients:
                del clients[client]
            client.close()

    #Server config
    bufferSize = 1024
    server = s.socket(s.AF_INET, s.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server started on {host}:{port}")

    #Server working cycle
    try:
        while True:
            client, client_addr = server.accept()
            print(f"Connection from {client_addr}")
            addr[client] = client_addr
            th.Thread(target=handle_client, args=(client,), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server.close()

##################################################################################Client functions
def client_func(host, port):
    global running
    running = True

    def receive_messages():
        while running:
            try:
                message = client.recv(bufferSize).decode("utf8")
                print(message)
            except OSError:
                break

    def send_messages():
        global running 
        print("Insert your username:")
        while running:
            try:
                message = input(">>")
                client.send(bytes(message, "utf8"))
                if message == "exit()":
                    client.close()
                    running = False
                    break
            except OSError:
                break

    #Client config
    client = s.socket(s.AF_INET, s.SOCK_STREAM)
    client.connect((host, port))
    print(f"Connected to server at {host}:{port}")

    #Client start-up
    th.Thread(target=receive_messages, daemon=True).start()
    send_messages()

##################################################################################Main
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python exercise_tcp_group_chat.py <server|client> <HOST> <PORT>")
        sys.exit(1)

    role = sys.argv[1].lower()
    host = sys.argv[2]
    port = int(sys.argv[3])

    if role == "server":
        server_func(host, port)
    elif role == "client":
        client_func(host, port)
    else:
        print("Invalid role. Allowed: 'server' or 'client'.")
        sys.exit(1)
