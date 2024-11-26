from snippets.lab3 import *
import sys, time

remote_peers: list[Client] = list()

def send_message(msg, sender):
    if len(remote_peers) == 0:
        print("No peer connected, message is lost")
    elif msg:
        for peer in remote_peers:
            peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def print_current_peers():
    if (len(remote_peers) == 0):
        print("No outgoing connection")
    else:
        print("Current outgoing connections:")
        for peer in remote_peers:
            print(f"\t{peer.local_address} -> {peer.remote_address}")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            if(connection in remote_peers):
                remote_peers.remove(connection)
                print_current_peers()
                connect_to_peer(peer_address=str(connection.remote_address[0]) + ":" + str(connection.remote_address[1]), 
                                waiting_time=10)
        case 'error':
            print(error)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            #remote_peers.append(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

port = int(sys.argv[1])
server = Server(port, on_new_connection)

def connect_to_peer(peer_address, waiting_time):
    try:
        remote_peer = Client(address(peer_address), on_message_received)
        print(f"Connected to {remote_peer.remote_address}")
        remote_peers.append(remote_peer)
    except ConnectionRefusedError:
        print(f"Can't connect to {peer_address}. Waiting {waiting_time} seconds before reconnection...")
        time.sleep(waiting_time)
        connect_to_peer(peer_address, waiting_time)

for peer in sys.argv[2:]:
    threading.Thread(connect_to_peer(peer, waiting_time=2), daemon=True).start()
    

username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        print("Shutting down...")
        break
