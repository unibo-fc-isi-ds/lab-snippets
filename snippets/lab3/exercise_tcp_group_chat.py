from snippets.lab3 import *
import sys

EXIT_MESSAGE = "*******LEAVES THE CHAT*******"

peers = set()

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
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
            peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

def send_message(msg, sender):
    if len(peers) == 0:
        print("No peer connected, message is lost")
    elif msg:
        for peer in peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

node = Server(int(sys.argv[1]), on_new_connection)

for peer in sys.argv[2:]:
    peers.add(Client(address(peer), on_message_received))

print(f'Local IP addresses: {list(local_ips())}')
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input(">")
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        send_message(EXIT_MESSAGE, username)
        break
node.close()
exit(0)
