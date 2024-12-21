import sys
import json
#print("ciao")
#sys.path.append("C:\Drawer2\2-Laurea-Magistrale\Distribuited System\lab-snippets\snippets")
from snippets.lab2 import address, local_ips, message
from snippets.lab3 import Client, Server
from snippets.lab3 import *

class GroupPeer():
    def __init__(self, port:int, peers=None, callback=None):
        self.receiver = Server(port, self.on_new_connection)
        self.peers:list[Client]
        self.peers = []
        if peers is not None:
            print(peers)
            peers_list = {peer for peer in peers}
            for peer_address in peers_list:
                client = Client(peer_address, self.on_message_received)
                self.peers.append(client)
            
            
    def broadcast_message(self, msg, sender):
        if len(self.peers) == 0:
            print("No peer connected, message is lost")
        elif msg:
            for peer in self.peers:
                peer.send(message(msg.strip(), sender)+MSG_ENCODE)
        else:
            print("Empty message, not sent")
                  
    
    def exit(self, sender):
        adr = self.receiver.local_address[0] +":"+ str(self.receiver.local_address[1])
        timestamp = datetime.now()
        for peer in self.peers:
                peer.send("\n" + adr + f" [{timestamp.isoformat()}]"+ EXIT_SEPARATOR +"\n"+ sender + EXIT_ENCODE)


    def remove_peer(self, member_to_remove):
            member_to_remove = next((member for member in self.peers if member == member_to_remove), None)
            if member_to_remove:
                self.peers.remove(member_to_remove)

        
    def on_message_received(self,event, payload, connection, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                self.remove_peer(connection)
                print(payload)
            case 'error':
                print(error)

  
    def on_new_connection(self, event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = self.on_message_received
                self.peers.append(connection)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)


# PROGRAM START HERE -----------------------------------

username = input('Enter your username to start the chat:\n')
port = int(sys.argv[1])
if len(sys.argv) > 2:
    peers = [address(peer) for peer in sys.argv[2:]]
    user = GroupPeer(port,peers)
else:            
    user = GroupPeer(port)
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')       

while True:
    try:
        content = input()
        print(f"{PREV_LINE}"+message(content)+f"{CLEAR_RIGHT}") # Clear input line and paste formatted message instead
        user.broadcast_message(content, username)
    except (EOFError, KeyboardInterrupt):
        user.exit(username)
        break
print("Bye bye, see you next time...")
user.receiver.close()
exit(0)