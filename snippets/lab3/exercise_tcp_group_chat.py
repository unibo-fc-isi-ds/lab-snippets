from snippets.lab3 import *
from typing import Set
import sys

remote_peers: Set[Client] = set()
EXIT_MESSAGE = "<LEAVES THE CHAT>"

def send_message(msg, sender):
    if not remote_peers:
        print("No peers connected, message is lost")
    elif msg.strip():
        for peer in remote_peers.copy():
            try:
                peer.send(message(msg.strip(), sender))
            except Exception as e:
                print(f"Failed to send message to {peer.remote_address}: {e}")
                remote_peers.remove(peer)
    else:
        print("Empty message, not sent")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            remote_peers.discard(connection)
        case 'error':
            print(f"Error with peer {connection.remote_address}: {error}")

port = int(sys.argv[1])

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[1]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Incoming connection from: {address}")
            connection.callback = on_message_received
            remote_peers.add(connection)
        case 'stop':
            print("Stopped listening for new connections")
        case 'error':
            print(f"Error on server: {error}")

server = Server(port, on_new_connection)

remote_endpoints = sys.argv[2:]

for remote_endpoint in remote_endpoints:
    try:
        peer = Client(address(remote_endpoint), on_message_received)
        print(f"Connected to {peer.remote_address}")
        remote_peers.add(peer)
    except ConnectionRefusedError:
        print(f"Connection refused for {remote_endpoint}")
    except TimeoutError:
        print(f"Timeout for {remote_endpoint}")
    except Exception as e:
        print(f"Error connecting to {remote_endpoint}: {e}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
try:
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    send_message(EXIT_MESSAGE,username)
    for peer in remote_peers.copy():
        peer.close()
    server.close() 