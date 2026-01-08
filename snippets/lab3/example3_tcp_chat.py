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

            # broadcast to all other peers
            for peer in peers:
                if peer is not connection:
                    peer.send(message(payload, sender="relay"))

        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            peers.discard(connection)
        case 'error':
            # ignora l'errore se il peer si è già chiuso
            if isinstance(error, OSError) and error.winerror == 10054:
                pass
            else:
                print(error)




def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Listening on port {address[0]} at {', '.join(local_ips())}")

        case 'connect':
            print(f"Incoming connection from {address}")
            connection.callback = on_message_received
            peers.add(connection)

        case 'stop':
            print("Stopped listening for new connections")

        case 'error':
            print(error)

if len(sys.argv) < 2:
    print("Usage: python peer.py <port> [peer1] [peer2] ...")
    sys.exit(1)

port = int(sys.argv[1])
known_peers = sys.argv[2:]

# start server
server = Server(port, on_new_connection)

# connect to known peers
for endpoint in known_peers:
    try:
        peer = Client(address(endpoint), on_message_received)
        peers.add(peer)
        print(f"Connected to peer {endpoint}")
    except Exception as e:
        print(f"Could not connect to {endpoint}: {e}")

# chat loop
username = input("Enter your username to start the chat:\n")
print("Type your message and press Enter to send it.")

try:
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    print("\nClosing connections...", flush=True)
    for peer in list(peers):
        peer.close()
    server.close()
