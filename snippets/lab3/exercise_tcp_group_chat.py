from snippets.lab3 import *
import sys

remote_peers: list[Client] = list()

def send_message(msg, sender):
    if len(remote_peers) == 0:
        print("No peer connected, message is lost")
    elif msg:
        for peer in remote_peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            for peer in remote_peers:
                if (peer != connection):
                    peer.send(payload)
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            remote_peers.remove(connection)
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            remote_peers.append(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

port = int(sys.argv[1])
server = Server(port, on_new_connection)

for peer in sys.argv[2:]:
    remote_peer = Client(address(peer), on_message_received)
    remote_peers.append(remote_peer)
    print(f"Connected to {remote_peer.remote_address}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        break
