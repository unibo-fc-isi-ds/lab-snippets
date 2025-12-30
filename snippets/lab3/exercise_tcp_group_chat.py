from snippets.lab3 import *
import sys


remote_peers : set[Connection] = set()


def send_message(msg, sender):
    global remote_peers
    if len(remote_peers) == 0:
        print("No peers connected, message is lost")
    elif msg:
        for remote_peer in remote_peers:
            try:
                remote_peer.send(message(msg.strip(), sender))
            except Exception as e:
                print(e)
    else:
        print("Empty message, not sent")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            global remote_peers; remote_peers.remove(connection)
        case 'error':
            print(error)

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


port = int(sys.argv[1])
server = Server(port, on_new_connection)
for endpoint in sys.argv[2:]:
    remote_peers.add(Client(address(endpoint), on_message_received))
for remote_peer in remote_peers:
    print(f"Connected to {remote_peer.remote_address}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for remote_peer in remote_peers.copy():
            remote_peer.close()
        break
server.close()
