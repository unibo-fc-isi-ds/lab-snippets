
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
                #client.send(str(port)+PORT_ENCODE)
                self.peers.append(client)
            
    
    def broadcast_message(self, msg, sender):
        if len(self.peers) == 0:
            print("No peer connected, message is lost")
        elif msg:
            for peer in self.peers:
                peer.send(message(msg.strip(), sender)+MSG_ENCODE)
        else:
            print("Empty message, not sent")
            
    def broadcast_list(self):
        peer_list = [peer.remote_address for peer in self.peers]
       # Serializza la lista dei peer
        encoded_list = json.dumps(peer_list)
        print(encoded_list)
        for peer in self.peers:
            print("sending...")
            peer.send(encoded_list+JSON_ENCODE)       
    
    def exit(self, sender):
        adr = self.receiver.local_address[0] +":"+ str(self.receiver.local_address[1])
        for peer in self.peers:
                peer.send("\n" + adr + EXIT_SEPARATOR +"\n"+ sender + EXIT_MESSAGE)

    def remove_peer(self, member_to_remove):
            member_to_remove = next((member for member in self.peers if member == member_to_remove), None)
            if member_to_remove:
                self.peers.remove(member_to_remove)
    
    def receive_list(self,encoded_list):
        print(encoded_list)
        decoded_list = json.loads(encoded_list)
        decoded_list = [tuple(item) for item in decoded_list]
        remote_peers = {peer.remote_address for peer in self.peers}
        print(f"list received: {decoded_list}")
        print(f"actual list {self.peers}")
        for peer in self.peers:
            print(peer.local_address)
        # Aggiungiamo solo gli oggetti con nomi non presenti
        #for peer in decoded_list:
        #    if peer not in remote_peers and peer != self.receiver.local_address:
        #        self.peers.append(Client(peer,self.on_message_received))
        #        remote_peers.add(peer)  # Aggiorna l'insieme dei nomi esistenti
        
        

        
    def on_message_received(self,event, payload, connection, error):
        match event:
            case 'message':
                print(payload)
            case 'update-list':
                print("updtlist")
                self.receive_list(payload)
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
                #connection.send()
                self.broadcast_list()
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

#def input_listener(event, result_container):
#    """Background thread function to get input."""
#    user_input = input()
#    result_container = user_input
#    event.set()  # Signal that input has been received
#
#           
#input_event = threading.Event()
#content=""
## Start a listener thread to get input in a non blocking way
#input_thread = threading.Thread(target=input_listener, args=(input_event, content))

username = input('Enter your username to start the chat:\n')
port = int(sys.argv[1])
if len(sys.argv) > 2:
    peers = [address(peer) for peer in sys.argv[2:]]
    user = GroupPeer(port,peers)
else:            
    user = GroupPeer(port)
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')       

#input_thread.start()
while True:
    
    #while not input_event.is_set():
        #input_event.wait(0.5)
        #if content:
            try:
                content = input()
                user.broadcast_message(content, username)
            except (EOFError, KeyboardInterrupt):
                user.exit(username)
                break
print("Bye bye, see you next time...")
user.receiver.close()
exit(0)


#class AsyncPeer():
#    def __init__(self, port:int, peers=None, callback=None):
#        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        self.socket.bind(address(port=port))
#        self.local_address = self.socket.getsockname()
#        self.port = port
#        self.__notify_closed = False
#        self.name = ""
#        self.peers: list[tuple[socket.socket,tuple[str,int]]]
#        self.peers = []
#        if peers is not None:
#            peers_list = {address(*peer) for peer in peers}
#            try:
#                for ip,port in peers_list:
#                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                    peer_socket.connect((ip, port))
#                    self.peers.append((peer_socket,(ip,port)))
#                    new_list = self.receive_peers_list(peer_socket)
#                    self.update_peers_list(new_list)
#                    threading.Thread(target=self.__handle_incoming_messages,args=(peer_socket, ip, port), daemon=True).start()
#            except Exception as e:
#                print(f"[ERRORE] Impossibile connettersi al peer {ip}:{port} - {e}")
#
#        self.__listener_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True)
#        self.__listener_thread.start()
#        
#
#    @property
#    def callback(self):
#        return self.__callback or (lambda *_: None)
#    
#    @property
#    def closed(self):
#        return self.socket._closed
#    
#    def setName(self,name):
#        if name is not None:
#            self.name = name
#                
#    def __handle_incoming_connections(self):
#        self.socket.listen()
#        self.on_command('listen', address=self.socket.getsockname())
#        try:
#            while not self.socket._closed:
#                incoming_socket = self.socket.accept()
#                if not any(incoming_socket in sockets for (sockets,_) in self.peers):
#                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                    peer_socket.connect(incoming_socket)
#                    self.peers.append((peer_socket,incoming_socket))
#                self.send_peers_list(peer_socket)
#                self.on_command('connect', address)              
#        except ConnectionAbortedError as e:
#            pass # silently ignore error, because this is simply the socket being closed locally
#        except Exception as e:
#            self.on_command('error', error=e)
#        finally:
#            self.on_command('stop')
#    
#    
#    def send_peers_list(self, client_socket):
#        peer_list = [address for (socket,address) in self.peers if address != (self.local_address, self.port)]  # Evita di inviare il proprio peer
#        # Serializza la lista dei peer
#        encoded_list = json.dumps(peer_list)
#        self.send(encoded_list,client_socket)
#    
#    def receive_peers_list(self):
#        encoded_list = self.receive()
#        decoded_list = json.loads(encoded_list)
#        decoded_list = [tuple(item) for item in decoded_list]
#        return decoded_list
#        
#    def update_peers_list(self, new_list):
#        return list(set(self.peers) | set(new_list))
#        
#    def remove_peer(self, addres_to_remove):
#            member_to_remove = next((member for member in self.peers if member[1][0] == addres_to_remove), None)
#            if member_to_remove:
#                self.peers.remove(member_to_remove)
#
#               
#    def __handle_incoming_messages(self):
#        try:
#            while not self.closed:
#                message = self.receive()
#                if message is None:
#                    break
#                if message.endswith(EXIT_MESSAGE):
#                    sender_addres,_ = message.split(EXIT_SEPARATOR)
#                    self.remove_peer(sender_addres)
#                self.on_command('message', message)
#        except Exception as e:
#            if self.closed and isinstance(e, OSError):
#                return # silently ignore error, because this is simply the socket being closed locally
#            self.on_command('error', error=e)
#        finally:
#            self.close()
#    
#    def on_command(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None):
#        self.__callback(event, connection, address, error)
#
#    def send(self, message, client_socket: socket.socket):
#        if not isinstance(message, bytes):
#            message = message.encode()
#            message = int.to_bytes(len(message), 2, 'big') + message
#        client_socket.sendall(message)
#    
#    def broadcast(self,message):
#        for socket in self.peers:
#            self.send(message,socket[0])
#    
#    def receive(self):
#        length = int.from_bytes(self.socket.recv(2), 'big')
#        if length == 0:
#            return None
#        return self.socket.recv(length).decode()
#    
#    def close(self):
#        self.socket.close()
#        if not self.__notify_closed:
#            message = f"{self.socket}{EXIT_SEPARATOR}{EXIT_MESSAGE}"
#            self.broadcast(message)
#            self.__notify_closed = True
#            
#    
#
###TODO: WIP
##def on_message_received(event, payload, sender: Peer, error):
##    match event:
##        case 'message':
##            print(payload)
##        case 'close':
##            print(f"{sender.name} has left the chat...")
##            global group_member; group_member = update_group_member(group_member,sender.local_address)
##        case 'error':
##            print(error)    
#
#
#  
#def send_message(msg, sender, local_peer:AsyncPeer):
#    if local_peer.peers is None:
#        print("The group is empty, message is lost")
#    elif msg:
#        local_peer.broadcast(message(msg.strip(), sender))
#    else:
#        print("Empty message, not sent")
#
#
#def on_event(event,address,error,payload=None):
#    match event:
#        case 'listen':
#            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
#        case 'connect':
#            print(f"Open ingoing connection from: {address}")    
#        case 'stop':
#            print(f"Stop listening for new connections")
#        case 'error':
#            print(error)
#        case 'message':
#            print(payload)
#        
#        
## PROGRAM START HERE  
#port = int(sys.argv[1])
#username = input('Enter your username to start the chat:\n')
#
#if sys.argv[2] is None:
#    local_peer = AsyncPeer(port,callback=on_event)
#    local_peer.setName(username)
#else:
#    local_peer = AsyncPeer(port,sys.argv[2],on_event)
#    local_peer.setName(username)
#    print(f"Connected from {sys.argv[2]}")
#
#print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
#
#while True:
#    try:
#        content = input()
#        send_message(content, username, local_peer)
#    except (EOFError, KeyboardInterrupt):
#        local_peer.close()