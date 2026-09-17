"""
-------------------------------------------------------------------------------
Student:    Gabriele Aprile
Exercise:   TCP Group Chat
Course:     Distributed Systems A.Y. 2025-2026


Goal:   support group chats in TCP
    - where clients may appear and disappear at any time
    - similarly to what happens for the UDP group chat example
    - in such a way each peer broadcasts messages to all the other peers it has been contacted with so far

Hints:
    - you can and should reuse the provided code, possibly modifying it
    - there's no need anymore to distinguish among servers and clients: all peers act simultaneously as both
    - peers may be informed about the endpoints of other peers at launch time (via command-line arguments)
-------------------------------------------------------------------------------
"""

from snippets.lab3 import *
import sys

# Local Port as first argument in cli
local_port = int(sys.argv[1])

# The other endpoints in the same connection passed starting from argument 2
# <LOCAL_PORT> <REMOTE_ADDR_1> <REMOTE_ADDR_2> ...
remote_endpoints = sys.argv[2:]

# List to memorize active peers in the connection
active_peers = []


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#| Support functions                                                            |#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
""" Send message to all connected endpoints """
def send_message(msg, sender):
    if active_peers is None:
        print("No peer connected, message is lost")
    elif msg:
        message_content = message(msg.strip(), sender)
        for p in active_peers:
            p.send(message_content)
    else:
        print("Empty message, not sent")


""" A callback for handling incoming messages """
def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)      # print any message received
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")   # inform the user the connection is closed
            if connection in active_peers:
                active_peers.remove(connection) # forget about the disconnected peer
        case 'error':
            print(f"Connection with peer {connection.remote_address} closed due to error: {error}")
            if connection in active_peers:
                active_peers.remove(connection) # forget about the peer


"""Server mode callback for handling ingoing connections """
def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Peer listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            active_peers.append(connection)         # New peer added on active_peer list
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#| Starting Server + connecting to peers specified in CLI                       |#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# Actually start the server
server = Server(local_port, on_new_connection)

for endpoint in remote_endpoints:
    try:
        new_peer = Client(address(endpoint), on_message_received) 
        active_peers.append(new_peer)
        print(f"Connected to: {endpoint}")
    except Exception as e:
        print(f"Error connecting to {endpoint}: {e}")


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#| User interface + message handling                                            |#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
# Get outgoing messages from the console and send them to the remote peers
username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        print("\n Leaving chat...")
        break

# Close remaining peers
for p in active_peers:
    p.close()
server.close()
