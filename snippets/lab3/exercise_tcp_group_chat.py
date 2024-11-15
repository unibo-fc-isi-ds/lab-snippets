from snippets.lab3 import *
import sys

mode = sys.argv[1].lower().strip()
peers = []

def send_message(msg, sender):
    ...

def on_message_received(event, paload, connection, error):
    ...

if mode == 'server':
    port = int(sys.argv[2])

    def on_new_connection(event, connection, address, error):
        ...

    server = Server(port, on_new_connection)

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
        if remote_peer:
            remote_peer.close()
        break
if mode == 'server':
    server.close()
