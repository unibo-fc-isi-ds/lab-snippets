from snippets.lab3 import *
import sys

EXIT_MESSAGE = "<LEAVES THE CHAT>"

def send_message(msg, sender):
    if not peer.peers:
        print("No peer connected, message is lost")
    elif msg:
        for p in peer.peers:
            p.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            peer.peers.discard(connection)
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            peer.peers.add(connection)
        case 'stop':
            print("Stop listening for new connections")
        case 'error':
            print(error)

class TCPPeer:
    def __init__(self, port):
        self.server = Server(port, on_new_connection)
        self.peers = set()


peer = TCPPeer(port=int(sys.argv[1]))

for target in sys.argv[2:]:
    try:
        c = Client(address(target), on_message_received)
        peer.peers.add(c)
    except Exception as e:
        print(f"couldnt connect to {target}: {e}")


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it.')

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        send_message(EXIT_MESSAGE, username)
        print(message(EXIT_MESSAGE, username))
        break

peer.server.close()