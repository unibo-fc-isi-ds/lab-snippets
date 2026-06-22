from snippets.lab2 import *
from snippets.lab3 import *
import sys


peers: list[Connection] = []

def send_message(msg, sender):
    if not peers:
        print("No peer connected, message is lost")
        return

    if msg:
        for peer in peers[:]:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if connection in peers:
                peers.remove(connection)
        case 'error':
            print(error)


def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            peers.append(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

port = int(sys.argv[1])
remote_endpoint = sys.argv[2] if len(sys.argv) > 2 else None

server = Server(port, on_new_connection)

if remote_endpoint:
    client_conn = Client(address(remote_endpoint), on_message_received)
    peers.append(client_conn)

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for peer in peers:
            peer.close()
        server.close()
        break