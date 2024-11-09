from snippets.lab3 import *
import sys

# group chat without central server
# peer informed of other peers at launch
# all peers act as both Server and Client

# Server socket used for receiving connetions/messages
# Client socket used for sending messages to all the peers
# Each peer is active, so it's a Client, but it is also passive, so it's a Server

# I need two sockets for each peer, one for sending the other for receiving
# I can't use the same socket because each peer actively connets to the others
# if one peer is the server and crashes, the group chat is over, but it shouldn't be

# The peer list is managed by the server socket, and used by the client socket to send messages
# Server socket immediately SHUTDW_WR, instead client immediately SHUTDW_RD
# The Server class uses thread and generate events when input is received
# Instead the Client sockets are used when the user writes input

remote_peers = []

### send messagge to all peers
def send_message(msg, sender):
    # check if the list is empty
    if remote_peers == []:
        print("No peer connected, message is lost")
    elif msg:
        # send to all peers
        for remote_peer in remote_peers: 
            remote_peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'messagae':
            print(payload)
        case 'close':
            # remove remote peer from the list
            print(f"Connection with peer {connection.remote_address} closed")
            client_to_remove = (client for client in remote_peers if client.remote_address == connection.remote_address)
            remote_peers.remove(client_to_remove) 
        case 'error':
            print(error)


def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                # add remote peer to the list
                print(f"Open ingoing connection from: {address}")
                # connection.callback = on_message_received
                remote_peers.append(Client (address, on_message_received))
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

port = int(sys.argv[1])
server = Server(port, on_new_connection)

remote_endpoints = [int(endp) for endp in sys.argv[2:]]
remote_peers = [Client(address(endp), on_message_received) for endp in remote_endpoints]
# print(f"Connected as Client to {peer.remote_address for peer in remote_peers}")

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        if remote_peers != []:
            for peer in remote_peers: peer.close()
        break
server.close()

