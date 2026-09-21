from snippets.lab3 import *
import sys

remote_peers = set()

def send_message(msg, sender):
    if not remote_peers:
        print("No peer connected, message is lost")
    elif msg:
        for peer in remote_peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            remote_peers.discard(connection)
        case 'error':
            if "10054" not in str(error): # Windows-specific error codes for connection reset/closed socket
                print(error)

port = int(sys.argv[1])

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            remote_peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

server = Server(port, on_new_connection)

remote_endpoints = sys.argv[2:]

for remote_endpoint in remote_endpoints:
    peer = Client(address(remote_endpoint), on_message_received)
    remote_peers.add(peer)
    print(f"Connected to {peer.remote_address}")


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        send_message("<LEAVES THE CHAT>", username)
        for peer in list(remote_peers):
            peer.close()
        break

server.close()
