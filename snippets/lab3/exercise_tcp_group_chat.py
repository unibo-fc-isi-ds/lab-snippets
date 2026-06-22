from snippets.lab3 import *
import sys
import time

#The goal is to implement a group chat via command line based on TCP. Since it is a peer to peer architecture,
# there's no need to distinguish between client and server anymore. Peers will also be informed about the endpoints of the other peers connected.

#First of all, we need to create a class Peer for the peers in the group chat: each object
#of the class has two different socket instances: one for the "server part", to receive
#the upcoming messages, and the other for the "client part", to send message to the other 
#peers. This class extends the Server class, while creating new methods in order to implement the
#client functionalities.

#We can create a list containing the endpoints of the peers that joined the group chat (that is, of the peer that have established a connection with allù
# the other peers already in the group chat). At the beginning, the list will be empty: no peer connected. Each time a peer connects with the other we 
# print via standard output the list with the endpoints of the other peers, then we add the one of the latest arrived peer.


EXIT = 'exit'
exit_message = 'I\'m leaving the chat now, bye!'
stop_chat_event = threading.Event() #I need to create a threading event so that when I set it, the different processes will not try to access the current socket anymore

class Peer(Server):
    def __init__(self, port, server_callback = None, client_callback = None):
        super().__init__(port, callback = server_callback)
        self.active_connections: list[Connection] = []
        self.client_cb = client_callback

    def connect_to(self, endpoint):
        ### 
        # method to establish the tcp connection with each of the peer connected to the chat, that are memorized in the active_connections field
        ###

        addr = endpoint
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sending_socket.bind(address(port=0))
        sending_socket.connect(addr)
        conn = Connection(sending_socket, callback = self.client_cb)
        self.active_connections.append(conn)
        return conn

    def close(self):
        ### 
        # method to close all the active connections of the peer: this method is called when the peer wants to close its connection and exit from the group chat
        ###

        for conn in self.active_connections:
            conn.close()
        self._Server__socket.close()
        

remote_peer : Peer | None = None
remote_endpoints: list = []

#the code requires for the peer to write as the 1st command line argument its address (ip, port)
latest_remote_endpoint = address(sys.argv[1])
_, port = latest_remote_endpoint

#to avoid dealing with duplicated endpoints
if latest_remote_endpoint not in remote_endpoints:
    remote_endpoints.append(latest_remote_endpoint)

for arg in sys.argv[2:]:
    ep = address(arg)
    if ep not in remote_endpoints:
        remote_endpoints.append(ep)

if (len(remote_endpoints) == 1):
    print(f"You are connected to the chat! You are the only one connected at the moment.")
else:
    print(f"You are connected to the chat! Here are the endpoints of the users connected to the group chat: ", remote_endpoints)


def send_message(msg, sender):
    if not remote_peer.active_connections:
        print("No peer connected, message is lost.")
    elif msg:
        for conn in remote_peer.active_connections:
            conn.send(message(msg.strip(), sender))
    else:
        print("Empty message, not sent.")

def on_message_received(event, payload, connection, error):
    if stop_chat_event.is_set():
        return
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed.")
            if connection in remote_peer.active_connections:
                remote_peer.active_connections.remove(connection)
            if connection.remote_address in remote_endpoints:
                remote_endpoints.remove(connection.remote_address)
        case 'error':
            if isinstance(error, socket.error) and error.errno in (10054, 104): #to avoid that whenever a user disconnects the OSerror is logged in the console.
                    pass 
            else:
                print(error)

def on_new_connection(event, connection, address, error):
        if stop_chat_event.is_set():
            return
        match event:
            case 'listen':
                print(f"Local peer listening on port {address[1]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"A new peer entered the chat! Its endpoint is: {address}")
                connection.callback = on_message_received
                remote_peer.active_connections.append(connection)
                if connection.remote_address not in remote_endpoints:
                 remote_endpoints.append(connection.remote_address)
                # print('Here\'s the updated list of the peers connected to the chat: ',remote_endpoints)
            case 'stop':
                print(f"Stop listening for new connections.")
            case 'error':
                print(error)

remote_peer = Peer(port, server_callback=on_new_connection, client_callback=on_message_received)

for addr in remote_endpoints:
    if addr != latest_remote_endpoint:
        remote_peer.connect_to(addr)

try:
    time.sleep(0.1) # this allows the showing first of the ips on which the peer is listening upon, and only after the log of the message asking the username. 
    username = input('Enter your username to start the chat:\n')
except (EOFError, KeyboardInterrupt):
        print('Username input interrupted.')
        username = None

if remote_peer and username:
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below. Type \'exit\' to leave the chat.')
    while True:
        try:
            content = input()
            if content == EXIT:
                if (len(remote_endpoints) > 1): #to avoid the printing of "No peer connected, message is lost.": if we already know that there is no other peer left in the chat we do not care.
                    send_message(exit_message, username) #if a user leaves the chat, a default exit messages will be sent to all the other peers in the chat
                    time.sleep(0.1) #in order to allow the the propagation of the exit message possible, since alternatively it would not be send before the setting of the close_chat_event
                break
            send_message(content, username)
        except (EOFError, KeyboardInterrupt): #even if a user shuts down the application by means of Ctrl+C/D, the exit message will be shown as well
            if (len(remote_endpoints) > 1): 
                    send_message(exit_message, username)
                    time.sleep(0.1)
            print('Chat input interrupted, exiting the chat.')
            break

if remote_peer:
    stop_chat_event.set()
    remote_peer.close()
    print('Connection has been closed!')
    remote_endpoints.remove(latest_remote_endpoint)
