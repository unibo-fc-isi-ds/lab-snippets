from typing import List
from snippets.lab3 import *
import sys

my_port = int(sys.argv[1])
multiPeers: List [Connection] = []


def send_message(msg, sender):
    if len(multiPeers) == 0 :
        print("No peer connected, message is lost")
    if msg:
        messageOne = message(msg.strip(), sender)
        for peer_conn in multiPeers:
                try:
                    peer_conn.send(messageOne)
                except Exception as e:
                    print(f"Error sending to{peer_conn.remote_address }: {e}")
            
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)         
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            try:
                multiPeers.remove(connection)
            except ValueError:
                pass
        case 'error':
            print(error)




def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = on_message_received
                multiPeers.append(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)




peers_to_connect = sys.argv[2:]

server = Server(my_port, on_new_connection)

for peers in peers_to_connect:
    try:
        client_connection = Client(address(peers), on_message_received)
        multiPeers.append(client_connection)
        print(f"connected to {peers}")
    except Exception as e:
        print(f"couldnt connect to {peers}: {e}")


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for conn in multiPeers:
            conn.close()
        server.close()
        break
