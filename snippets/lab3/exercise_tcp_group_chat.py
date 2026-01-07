#python snippets\lab3\tcp_group_chat.py 8080 - configure peer A to listen on port 8080
#python snippets\lab3\tcp_group_chat.py 8081 localhost:8080 - start peer B on port 8081 and connect it to a remote peer on port 8080
from snippets.lab3 import *
import sys, time

remote_peer_connections: dict[tuple[str, int], Connection] = {}

def send_message(msg, sender):
    if not msg:
        print("Empty message, not sent")
        return
    
    if not remote_peer_connections:
        print("No peer connected, message is lost")
    else:
        for connection in remote_peer_connections.values():
            if sender:
                connection.send(message(msg.strip(), sender))
            else:
                connection.send(msg)

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            global remote_peer_connections
            if connection.remote_address in remote_peer_connections:
                del remote_peer_connections[connection.remote_address]
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open new connection with {address}")
            connection.callback = on_message_received
            global remote_peer_connections
            remote_peer_connections[address] = connection
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

port = int(sys.argv[1])
remote_endpoint_tuple = [] 
if len(sys.argv) >= 3:
    remote_endpoints_str_list = sys.argv[2:] 
    for addr in remote_endpoints_str_list:
        remote_endpoint_tuple.append(address(addr))
    local_peer = Peer(port, on_new_connection, remote_endpoint_tuple)
else:
    local_peer = Peer(port, on_new_connection)
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        send_message(username + ' leaves the chat', None)
        break

local_peer.close()
