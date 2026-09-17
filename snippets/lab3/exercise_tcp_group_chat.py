from snippets.lab3 import *
import sys

remote_peers = []

def send_message(msg, sender):
    if not remote_peers:
        print("No peer connected, message is lost")
    elif msg:
        for remote_peer in remote_peers:
            try:
                remote_peer.send(message(msg.strip(), sender))
            except Exception as e:
                print(f"Error sending to {remote_peer.remote_address}: {e}")
                remote_peers.remove(remote_peer)
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if connection in remote_peers:
                remote_peers.remove(connection)
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[1]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = on_message_received
                global remote_peers
                remote_peers.append(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

if len(sys.argv) < 2:
    sys.exit(1)

local_connection = int(sys.argv[1])

remote_connections = sys.argv[2:] if len(sys.argv) > 2 else None

server = Server(local_connection, on_new_connection)

if remote_connections:
    for connection in remote_connections:
        remote_peers.append(Client(address(connection), on_message_received))

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for remote_peer in remote_peers:
            if remote_peer:
                remote_peer.close()
        break
server.close()