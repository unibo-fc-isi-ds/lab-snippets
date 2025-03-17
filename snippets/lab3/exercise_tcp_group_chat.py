from snippets.lab3 import *
import sys

peer_connected = []

def broadcast_message(msg, sender):
    if not peer_connected:
        print("No peer connected, message is lost")
    if msg:
        for peer in peer_connected:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            #global peer_connected; peer_connected = None
        case 'error':
            print(error)

def server_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            peer_connected.remove(connection)
        case 'error':
            print(error)

port = int(sys.argv[1])

def on_new_connection(event, connection, address, error):
    match event:
        case 'connect':
            print(f"Peer connected: {address}")
            connection.callback = server_received
            global remote_peer; remote_peer = connection
            peer_connected.append(remote_peer)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)


username = input('Enter your username to start the chat:\n')

server = Server(port, on_new_connection)

print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')


remote_endpoint = sys.argv[2:]

for peer in remote_endpoint:
    remote_peer = Client(address(peer), on_message_received)
    peer_connected.append(remote_peer)
    print(f"Connected to {remote_peer.remote_address}")

while True:
    try:
        content = input()
        broadcast_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for remote_peer in peer_connected:
            remote_peer.close()
        server.close()
        break
server.close()
