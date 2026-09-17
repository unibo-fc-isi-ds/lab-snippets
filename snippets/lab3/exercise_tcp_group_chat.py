from snippets.lab3 import *
import sys

remote_peers: list[Client] = [] # There is now more than a single peer, inizialize an empty
# list that will be filled by connections of each peers

def broadcast_message(msg, sender, exclude=None):
    if not remote_peers:
        print("No peer connected, message is lost: wait for someone")
    elif msg.strip(): # If msg is not empty or filled of white space...
        for peer in remote_peers: # Brodcasting
            if peer != exclude: # Not sending message to, for example himself
                peer.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent")

def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
                print(payload) # print any message recived
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed") # inform the user the connection is closed
            if connection in remote_peers:
                remote_peers.remove(connection) # removing the connection of disconnected peer from the remote_peers list
        case 'error':
            if "10054" in str(error): # That's an error in windows when a peer leaves, but the exit of a peer is managed in another
                # way in the program so I dont wanna see this error
                pass
            else:
                print(error)


def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received # attach callback to the new connection
            #global remote_peer; remote_peer = connection # assign the new connection to the global variable
            remote_peers.append(connection) # Add to list the connection
        case 'stop':
            print(f"Stop listening for new connections")
        case 'error':
            print(error)

def connect_to_peers(endpoints):
    for endpoint in endpoints:    
        try: 
            peer = Client(address(endpoint), on_message_received)
            remote_peers.append(peer)
        except Exception as e:
            print(f"Error while connecting to {endpoint}: {e}")


# "main"
local_port = int(sys.argv[1]) # First argument in command line is the local port of each peer
server = Server(local_port, on_new_connection)
connect_to_peers(sys.argv[2:]) # Other argument are the peers to connect with

print("Welcome, to exit the chat u can use the special message 'exit()'")
username = input('Enter your username to start the chat:\n>')
print('Type your message and press Enter to send it. \nMessages from other peers will be displayed below...\n>', end="")
while True:
    try:
        content = input()
        if (content=="exit()"):
            if remote_peers: # if someone is present
                broadcast_message("Yo guys I'm leaving...", username) # Just for fun managing with a default message the exit case
            for peer in remote_peers:
                peer.close()
            server.close()
            break
        broadcast_message(content, username) # sends the message to other peers in the remote_peers list
    except (EOFError, KeyboardInterrupt): # On windows this iss strange it prints some errors in terminal, for cleaner execution
        # just use special message "exit()" to close the chat for a peer
        for peer in remote_peers:
            peer.close()
        server.close()
        break

# To run:
    # poetry run python ./snippets/lab3/exercise_tcp_group_chat.py LOCALPORT [PEER_1_IP:PORT PEER_2_IP:PORT ...]

# ** Peers have to be informed about the endpoints of otger peers at launch time (via command-line arguments)
# ** PEER_N_IP easly find by taping "ipconfig" in cmd and looking for IPv4 (or just localhost), 
# obviously the chat group can be runned only under the same wifi unless we put the application in a real server 

# example of execution:
    # poetry run python ./snippets/lab3/exercise_tcp_group_chat.py 8080
    # poetry run python ./snippets/lab3/exercise_tcp_group_chat.py 8081 localhost:8080
    # poetry run python ./snippets/lab3/exercise_tcp_group_chat.py 8082 localhost:8080 localhost:8081
    # .
    # .
    # .
    # poetry run python ./snippets/lab3/exercise_tcp_group_chat.py 808(n-1) localhost:8080 ... localhost:808(n-2)