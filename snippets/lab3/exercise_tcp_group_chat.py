from snippets.lab3 import *
import sys


# mode = sys.argv[1].lower().strip()
remote_peers = set()


def send_message(msg, sender):
    if not remote_peers:
        print("No peer connected, message is lost")
    elif msg:
        for remote_peer in remote_peers:
            remote_peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            global remote_peers; remote_peers.discard(connection)
        case 'error':
            print(error)

#if mode == 'server':
def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            global remote_peers; remote_peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

    
#elif mode == 'client':
port = int(sys.argv[1])
server = Server(port, on_new_connection)
remote_endpoints = sys.argv[2:]
for remote_endpoint in remote_endpoints:
    remote_peer = Client(address(remote_endpoint), on_message_received)
    #remote_peer.callback = on_message_received
    remote_peers.add(remote_peer)
    print(f"Connected to {remote_peer.remote_address}")
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for peer in list(remote_peers):
            peer.close()
        break
#if mode == 'server':
server.close()
