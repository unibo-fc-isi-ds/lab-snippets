from snippets.lab3 import *
import sys

#Server have a set of connected clients
clients = set()


def broadcastmsg(user,msg):
    if clients:
        for c in clients.copy():
            try:
                c.send(message(msg.strip(),user))
            except Exception as e:
                print("Something bad happened : " + e)
                clients.remove(c)  # Remove faulty connection
            


def send_message(msg, sender):
    if not clients:
        print("No peer connected, message is lost")
    elif msg:
        broadcastmsg(sender,msg)#Send msg to all connected clients
    else:
        print("Empty message, not sent")


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload) 
        case 'close':
            clients.discard(connection)
            print(f"Connection with peer {connection.remote_address} closed")
        case 'error':
            print(error)
            if connection in clients:
                clients.remove(connection)# Remove disconnected peer 

def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = on_message_received
                clients.add(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)
                
def connect_to_peer(endpoint):
    try:
        remote_peer = Client(address(endpoint), on_message_received)
        clients.add(remote_peer)  # Add the remote peer to the set of connections
    except Exception as e:
        print(f"Failed to connect to peer at {endpoint}: {e}")
        sys.exit(1) 
        

if len(sys.argv) < 2:
    print("Need at least a port number")
    sys.exit(1)

#Start Server 
port = int(sys.argv[1])
server = Server(port, on_new_connection)


#check if it's a client
remote_endpoint = sys.argv[2] if len(sys.argv) > 2 else None
if remote_endpoint:
    connect_to_peer(remote_endpoint)
     


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

try:
    while True:
        content = input()
        send_message(content, username)
except (EOFError, KeyboardInterrupt):
    send_message("\nDisconneting\n",username)
    # Close all client connections
    if clients:
        for c in clients.copy():
            c.close()
    # Stop the server
    print("Disconnected.")     
    server.close()
    


