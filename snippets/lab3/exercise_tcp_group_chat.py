from snippets.lab3 import *
import sys

# Execution mode
operation_mode = sys.argv[1].lower().strip()

# Lists for connected clients and remote connection initialization
connected_clients = []  
remote_peer = None 


def handle_message_received(event_type, data, connection, error):
    match event_type:
        case 'error': 
            print (f"Error: {error}")
        case 'message':
            print(data)
            # Propagate the message to all clients except the sender
            for c in connected_clients :
                # Check that the message is not sent to the sender themselves
                # if he does it as an exception, otherwise he sends the message
                if c != connection:
                    try:
                        c.send(f"{connection.remote_address}: {data}")
                    except Exception as exc:
                        print(f"Error sending message to {c.remote_address}: {exc}")
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if connection in connected_clients :
                connected_clients .remove(connection)

def broadcast_message(message, sender_name):
    if operation_mode == 'server':
        if message: 
            for c in connected_clients:
                try :
                    c.send(f"{sender_name}: {message}")
                except Exception as exc:
                    print(f"Error sending message to {c.remote_address}: {exc}")
        else:
            print("Empty message, not sent")
    elif operation_mode == 'client':
        if remote_peer is None:
            print("No peer connected, message is lost")
        elif message:
            remote_peer.send(f"{sender_name}: {message}")
        else:
            print("Empty message, not sent")

if operation_mode == 'server':
    server_port = int(sys.argv[2])

    def manage_new_connection(event, connection, address, error):
        match event:
            case 'error':
                print(f"Server error: {error}")
            case 'listen':
                print(f"Server listening on port {address[1]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"New connection from: {address}")
                connection.callback = handle_message_received
                connected_clients.append(connection)
            case 'stop':
                print("Server stopped listening for new connections")

    server = Server(server_port, manage_new_connection)

elif operation_mode == 'client':
    remote_endpoint = sys.argv[2]

    remote_peer = Client(address(remote_endpoint), handle_message_received)
    print(f"Connected to server at {remote_peer.remote_address}")

# start
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

try:
    while True:
        user_input = input()
        broadcast_message(user_input, username)
except (EOFError, KeyboardInterrupt):
    if remote_peer:
        remote_peer.close()
    if operation_mode == 'server':
        for c in connected_clients:
            c.close()
        server.close()
    print("Chat closed.")
