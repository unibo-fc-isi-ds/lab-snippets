from snippets.lab3 import *
import sys

remote_peers = set()

def send_message(msg, sender):
    if not remote_peers:
        print("No peer connected, message is lost")
    elif msg:
        for peer in remote_peers:
            peer.send(message(msg.strip(), sender))
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
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            global remote_peers; remote_peers.add(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)
            

listening_port = int(sys.argv[1])
server = Server(listening_port, on_new_connection)

remote_endpoints = sys.argv[2:]
for endpoint in remote_endpoints:
    client = Client(address(endpoint), on_message_received)
    remote_peers.add(client)
    print(f"Connected to {client.remote_address}")
    
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        peers_to_close = list(remote_peers)
        for peer in peers_to_close:
            peer.close()
        break

server.close()