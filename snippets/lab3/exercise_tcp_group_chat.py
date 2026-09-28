from snippets.lab3 import *
import sys

remote_peers: dict[tuple, Connection] = {}

def send_message(msg, sender):
    if len(remote_peers) == 0:
        print("No peer connected, message is lost")
    elif msg: 
        for remote_peer in remote_peers.values():
            remote_peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            global remote_peers
            if connection.remote_address in remote_peers.keys():
                remote_peers.pop(connection.remote_address)
                print(f"Connection with peer {connection.remote_address} closed")
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            global remote_peers
            remote_peers[address] = connection
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)


nConnections = len(sys.argv) - 2
port = int(sys.argv[1])
self = Peer(port, on_new_connection)

for i in range(2, nConnections+2):
    try:
        remote_address = sys.argv[i].strip()
        parts = remote_address.split(':')
       
        conn = Connection(None, address(remote_address), on_message_received)
        print(f"Connected to {remote_address}")
        
        remote_peers[(parts[0], int(parts[1]))] = conn
    except Exception as e:
        print(f"Failed to connect to {remote_address}: {e}")



username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        if len(remote_peers) > 0:
          
            for remote_peer in list(remote_peers.values()): #closes the connection between other peers
                remote_peer.close()
        break

self.close()

