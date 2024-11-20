from snippets.lab3 import *
import sys


mode = sys.argv[1].lower().strip()
remote_peer: list[Client] | list[Server] = []


def send_message(msg, sender):
    if not remote_peer:
        print("No peer connected, message is lost")
    elif msg:
        for peer in remote_peer:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def message_forward(msg, connection_with_sender):
    if not remote_peer:
        print("No peer connected, message is lost")
    elif msg:
        for peer in remote_peer:
            if peer != connection_with_sender:
                peer.send(msg)
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            global remote_peer; remote_peer.remove(connection)
        case 'error':
            print(error)

def on_message_received_server(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
            message_forward(payload, connection)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            message_forward(f"Connection with peer {connection.remote_address} closed", connection)
            global remote_peer; remote_peer.remove(connection)
        case 'error':
            print(error)

if mode == 'server':
    port = int(sys.argv[2])

    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = on_message_received_server
                global remote_peer; remote_peer.append(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

    server = Server(port, on_new_connection)
elif mode == 'client':
    remote_endpoint = sys.argv[2]

    remote_peer.append(Client(address(remote_endpoint), on_message_received))
    print(f"Connected to {remote_peer[0].remote_address}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        if remote_peer:
            for peer in remote_peer:
                peer.close()
        break
if mode == 'server':
    server.close()
