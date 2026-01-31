from snippets.lab3 import *
import sys

def cleanup():
    print("\nExiting chat, closing connections...")
    for peer in list(peers):
        try:
            send_message("[System] Peer is disconnecting...", peer.remote_address)
            peer.close()
        except Exception as e:
            print(f"Could not close connection to {peer.remote_address}: {e}")

    server.close()

def send_message(msg, sender):
    if len(peers) == 0:
        print("No peer connected, message is lost")
    elif msg:
        for peer in list(peers):
            try:
                peer.send(message(msg.strip(), sender))
            except Exception as e:
                print(f"Could not send message to {peer.remote_address}: {e}")
                peers.remove(peer)
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            peers.remove(connection)
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Opening ingoing connection from: {address}")
            connection.callback = on_message_received
            peers.add(connection)
            send_message(f"[System] New peer connected: {address}", connection.remote_address)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

my_port = int(sys.argv[1])
server = Server(int(sys.argv[1]), on_new_connection)

peers = set()

for peer_address in sys.argv[2:]:
    try:
        peer = Client(address(peer_address), on_message_received)
        print(f"Connected to {peer.remote_address}")
        peers.add(peer)
    except Exception as e:
        print(f"Could not connect to {peer_address}: {e}")
        peers.remove(peer_address)

try:
    username = input('Enter your username to start the chat:\n')
except (EOFError, KeyboardInterrupt):
    cleanup()
    sys.exit(0)
    
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        send_message(input(), username)
    except (EOFError, KeyboardInterrupt):
        break

cleanup()