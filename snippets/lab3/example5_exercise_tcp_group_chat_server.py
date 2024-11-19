import time
from typing import List
from snippets.lab3 import *
import sys

remote_peers: List[Client] = []

def forward_message(msg, sender_connection):
    if msg:
        for peer in remote_peers:
            if peer != sender_connection:
                peer.send(msg)
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(f"Inoltro a tutti il messaggio: {payload}")
            forward_message(payload, connection)
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
            global remote_peers; remote_peers.append(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

port = int(sys.argv[1])
server = Server(port, on_new_connection)

while True:
    try:
        time.sleep(1)
        continue
    except (EOFError, KeyboardInterrupt):
        if remote_peers:
            remote_peers.close()
        break
server.close()