from snippets.lab3 import *
import sys
import time

port = int(sys.argv[1])
remote_endpoints = sys.argv[2:]
print(f'Port selected is {port} endpoints: {remote_endpoints}')
remote_peers: set[Connection] = set()

def send_message(msg, sender):
    if len(remote_peers) == 0:
        print("No peers connected, message is lost")
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

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {port} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            global remote_peers
            if not any(conn.remote_address == connection.remote_address for conn in remote_peers):
                connection.callback = on_message_received
                remote_peers.add(connection)
            else:
                connection.close()
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

username = input('Enter your username to start the chat:\n')

for remote_endpoint in remote_endpoints:
    remote_peer = Client(address(remote_endpoint), on_message_received)
    remote_peers.add(remote_peer)
    print(f"Connected to {remote_peer.remote_address}")

server = Server(port, on_new_connection)
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for remote_peer in list(remote_peers):
            remote_peer.close()
        server.close()
        break

# Waits for all thread to stop
time.sleep(1)
sys.exit(0)