from snippets.lab3 import *
import sys

# -------------------- Helper functions --------------------

# Prepare message by adding sender info
def send_message(msg, sender):
    if client is None:
        print("Server not connected, message is lost\n")
    elif msg:
        client.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent\n")

# Broadcast message to all connected clients except the sender
def broadcast(msg, sender):
    for peer in client_list:
        if peer is not sender:
            peer.send(msg)

# -------------------- Event handlers --------------------

# Handle events for server-side connections
def on_message_received_server(event, payload, connection, error):
    match event:
        case 'message':
            print('\n' + payload + '\n')
            broadcast(payload, connection)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed\n")
            broadcast(f"User {connection.remote_address} left the chat", connection)
            client_list.discard(connection)
        case 'error':
            print(error)

# Handle events for client-side connections
def on_message_received_client(event, payload, connection, error):
    match event:
        case 'message':
            print('\n' + payload + '\n')
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed\n")
            global client; client = None
        case 'error':
            print(error)

# -------------------- Main program --------------------

mode = sys.argv[1].lower().strip()
client: Client | None = None
client_list: set[Client] | None = None

# -------------------- Server mode --------------------
if mode == 'server':
    client_list = set()
    port = int(sys.argv[2])

    # Handle events for server itself
    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}\n")
            case 'connect':
                print(f"Open ingoing connection from: {address}\n")
                connection.callback = on_message_received_server
                broadcast(f"User {connection.remote_address} joined the chat", connection)
                client_list.add(connection)
            case 'stop':
                print(f"Stop listening for new connections\n")
            case 'error':
                print(error)

    server = Server(port, on_new_connection)
    try:
        print('Use Ctrl+C or type "!Shutdown" to stop the broker.\n')
        while True:
            content = input()
            if content.strip().lower() == '!shutdown':
                break
            print('Type your message and press Enter to send it.\n')
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        broadcast("Server is shutting down, connection will be closed.", "Server")
        for peer in client_list.copy():
            peer.close()
        server.close()

# -------------------- Client mode --------------------
elif mode == 'client':
    remote_endpoint = sys.argv[2]
    try:
        client = Client(address(remote_endpoint), on_message_received_client)
    except ConnectionRefusedError:
        print("Server refused connection\n", file=sys.stderr)
        sys.exit(1)
    print(f"Client connected to {client.remote_address}\n")

    try:
        username = input('Enter your username to start the chat:\n')
        print('Type your message and press Enter to send it. Messages from other peers will be displayed below.\n')
        while True:
            content = input()
            if content.strip().lower() == '!shutdown':
                break
            send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        if client:
            client.close()