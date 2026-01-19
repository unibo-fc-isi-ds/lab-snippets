from snippets.lab3 import *
import sys


peers: set[Client] = set()


def send_message(msg, sender):
    if not msg:
        print("Empty message, not sent")
        return
    for peer in peers:
        peer.send(message(msg.strip(), sender))


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
            for peer in peers:
                if peer != connection:
                    peer.send(message(payload, sender="relay"))

        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            peers.discard(connection)

        case 'error':
            # Windows: client closed abruptly
            if isinstance(error, ConnectionResetError) or (
                isinstance(error, OSError) and getattr(error, "winerror", None) == 10054
            ):
                peers.discard(connection)
            else:
                print(error)

            


def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Opening ingoing connection from: {address}")
            connection.callback = on_message_received
            peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

if len(sys.argv) < 2:
    print("Usage:")
    print("  Server: python exercise_tcp_group_chat.py <port>")
    print("  Client: python exercise_tcp_group_chat.py <port> <peer1> [peer2 ...]")
    sys.exit(1)

port = int(sys.argv[1])

known_peers = []
if len(sys.argv) > 2:
    known_peers = sys.argv[2:]


server = Server(port, on_new_connection)

for endpoint in known_peers:
    try:
        peer = Client(address(endpoint), on_message_received)
        peers.add(peer)
        print(f"Connected to {peer.remote_address}")
    except Exception as e:
        print(f"Could not connect to {endpoint}: {e}")
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        print("Shutting down...")
        for peer in list(peers):
            peer.close()
        peers.clear()

        server.close()
        break
