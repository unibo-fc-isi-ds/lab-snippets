from snippets.lab3 import *
import sys

mode = sys.argv[1].lower().strip()
peers: set[Client] = set()

def send_message(msg, sender):
    if peers is None:
        print("No peer connected, message is lost")
    elif msg:
        for peer in peers:
            if peer != sender:
                peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
            if mode == 'server': send_message(payload, connection)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            peers.remove(connection)
        case 'error':
            print(error)

if mode == 'server':
    port = int(sys.argv[2])

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

    server = Server(port, on_new_connection)

elif mode == 'client':
    remote_endpoint = sys.argv[2]
    peer = Client(address(remote_endpoint), on_message_received)
    peers.add(peer)
    print(f"Connected to {peer.remote_address}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

try:
    # Chat loop
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    if peers:
        for peer in peers:
            peer.close()
    if mode == 'server':
        for peer in peers:
            peer.close()
        server.close()
    print("Chat closed.")
