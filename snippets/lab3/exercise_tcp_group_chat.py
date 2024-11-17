import sys


from snippets.lab3 import *


def send_message(msg, sender):
    if not client_list:     # the list of client is empty
        print("No peer connected, message is lost")
    elif msg:
        for remote_peer in client_list:
            remote_peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            for remote_peer in client_list:
                if remote_peer.remote_address == connection.remote_address:
                    client_list.remove(remote_peer)
                    break
                print(f"Connection with peer {connection.remote_address} closed")
        case 'error':
            print(error)


def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[1]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            global client_list; client_list.append(connection)
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            import traceback
            traceback.print_exc(error)
            print(error)


port = int(sys.argv[1])

client_list = []  # List of known clients


server = Server(port, on_new_connection)  # Every client has a server

if len(sys.argv) > 2:
    client_list = [Client(address(remote_endpoint), on_message_received) for remote_endpoint in sys.argv[2:]] 

    # connection check
    for remote_peer in client_list:
        print(f"Connected to {remote_peer.remote_address}")


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        if client_list:
            for remote_peer in client_list:
                remote_peer.close()
        break

server.close()
