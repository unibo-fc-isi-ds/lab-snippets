import sys
from snippets.lab3 import *
peers_lock = threading.Lock()
# imitate the attribute peers in the lab2 example
peers: set[Connection] = set()

def send_group_message(msg, sender):
    with peers_lock:
        if len(peers):
            if msg:
                closed_peers = []
                for connection in peers:
                    if connection.closed:
                        closed_peers.append(connection)
                        continue
                    connection.send(message(msg.strip(), sender))
                for closed in closed_peers:
                    peers.discard(closed)
            else:
                print("Empty message, not sent")
        else:
            print("No peers connected, message is lost")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            with peers_lock:
                peers.discard(connection)
        case 'error':
            print(error)


def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            with peers_lock:
                peers.add(connection)
        case 'stop':
            print(f"Stop listening for new peers")
        case 'error':
            print(error)

port = int(sys.argv[1])
remote_endpoint_list: list[str] = sys.argv[2:]
server = Server(port, on_new_connection)

for remote_endpoint in remote_endpoint_list:
    peer = Client(address(remote_endpoint), on_message_received)
    print(f"Connected to {peer.remote_address}")
    with peers_lock:
        peers.add(peer)

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_group_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for peer in peers:
            with peers_lock:
                peer.close()
        break
server.close()