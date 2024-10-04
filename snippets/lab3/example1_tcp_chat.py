from snippets.lab2 import address, message, local_ips
from snippets.lab3 import *
import sys


mode = sys.argv[1].lower().strip()
remote_peer: Client = None


def send_message(msg, sender):
    if remote_peer is None:
        print("No peer connected, message is lost")
    elif msg:
        remote_peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(payload, sender, error):
    if error is not None and not isinstance(error, OSError):
        print(f"An {type(error).__name__} occurred: {error}")
    if payload is None and sender is not None:
        print(f"Peer {sender} has disconnected")
    if payload is not None:
        print(payload)


if mode == 'server':
    port = int(sys.argv[2])

    def on_new_connection(connection, address):
        print(f"Start conversation with peer {address}")
        connection.callback = on_message_received
        global remote_peer; remote_peer = connection

    server = Server(port, on_new_connection)
    print(f"Server listening on port {port} at {", ".join(local_ips())}")
elif mode == 'client':
    remote_endpoint = sys.argv[2]

    remote_peer = Client(address(remote_endpoint), on_message_received)
    print(f"Connected to {remote_peer.remote_address}")


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        remote_peer.close()
        break
if mode == 'server':
    server.close()
