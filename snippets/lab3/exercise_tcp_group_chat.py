from snippets.lab3 import *
import sys
import threading

mode = sys.argv[1].lower().strip()

clients = []  
lock = threading.Lock()  

def broadcast_message(msg, sender):
    with lock:
        for client in clients:
            try:
                client.send(f"{sender}: {msg}")
            except Exception as e:
                print(f"Error broadcasting message to {client.remote_address}: {e}")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
            broadcast_message(payload, connection.remote_address)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            with lock:
                if connection in clients:
                    clients.remove(connection)
        case 'error':
            print(f"Error: {error}")

def send_message(msg, sender):
    if remote_peer is None:
        print("No peer connected, message is lost")
    elif msg:
        remote_peer.send(f"{sender}: {msg}")
    else:
        print("Empty message, not sent")

if mode == 'server':
    port = int(sys.argv[2])

    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[1]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"New connection from: {address}")
                connection.callback = on_message_received
                with lock:
                    clients.append(connection)
            case 'stop':
                print("Server stopped listening for new connections")
            case 'error':
                print(f"Server error: {error}")

    server = Server(port, on_new_connection)

elif mode == 'client':
    remote_endpoint = sys.argv[2]

    remote_peer = Client(address(remote_endpoint), on_message_received)
    print(f"Connected to server at {remote_peer.remote_address}")

# start
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

try:
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    if remote_peer:
        remote_peer.close()
    if mode == 'server':
        with lock:
            for client in clients:
                client.close()
        server.close()
    print("Chat closed.")
