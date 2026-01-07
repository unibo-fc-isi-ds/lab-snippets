from snippets.lab3 import *
import sys

active_peers: list = []

def send_message(msg,sender):
    if not active_peers:
        print("No peer connected, message lost")
    elif msg:
        for peer in active_peers:
            try:
                peer.send(message(msg.strip(),sender))
            except Exception as e:
                print(f"Error sending to {getattr(peer,'remote_address','(unknown)')}: {e}")
    else:
        print("Empty message, message not sent")

def on_message_received(event,payload,connection,error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if connection in active_peers:
                active_peers.remove(connection)
        case 'error':
            print(error)

def on_new_connection(event,connection,address,error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', cd'.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            active_peers.append(connection)
            connection.callback = on_message_received
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

if len(sys.argv) < 2:
    print("Usage: python exercise_tcp_group_chat.py <server_port> <remote_endpoint1> [<remote_endpoint2> ...]")
    sys.exit(1)

server_port = int(sys.argv[1])
remote_endpoints = sys.argv[2:]

server = Server(server_port, on_new_connection)

for endpoint in remote_endpoints:
    try:
        peer_conn = Client(address(endpoint),on_message_received)
        active_peers.append(peer_conn)
        print(f"Connected to {peer_conn.remote_address}")
    except Exception as e:
        print(f"Could not connect to {endpoint}: {e}")

username = input('WELOME TO THE D.S. GROUP CHAT! Please enter your username to join the conversation:\n')
print('Type your message and press Enter to send it in the chat. Below you can see messages from other peers.')

try:
    while True:
        try:
            content = input()
            send_message(content,username)
        except(EOFError, KeyboardInterrupt):
            break
finally:
    for peer in active_peers:
        try:
            peer.close()
        except Exception:
            pass
    server.close()