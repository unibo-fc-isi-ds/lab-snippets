import socket
import threading
import sys
import json
import time
import selectors
import ipaddress

class TCPChatUser:
    def __init__(self, name, address, port, known_users=None):
        self.name = name
        self.port = port
        self.address = address
        self.peers = {}
        self.selector = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.is_online = True
        threading.Thread(target=self._accept_connection, daemon=True).start()
        threading.Thread(target=self._listen_for_peers, daemon=True).start()
        if known_users:
            self._connect_to_known_users(known_users)

    def _accept_connection(self):
        try:
            while self.is_online:
                client_socket, addr = self.server_socket.accept()
                client_socket.setblocking(False)
                self.peers[client_socket] = []
                self.selector.register(client_socket, selectors.EVENT_READ, self._handle_peer)
        except OSError as e:
            pass

    def _listen_for_peers(self):
        try:
            while self.is_online:
                if self.selector.get_map():
                    events = self.selector.select(timeout=1)
                    for key, mask in events:
                        callback = key.data
                        callback(key.fileobj)
        except OSError as e:
            pass

    def _handle_peer(self, client_socket):
        try:
            # Read the length of the message (first 4 bytes)
            raw_msglen = self._recvall(client_socket, 4)
            if not raw_msglen:
                raise Exception("Error in reading message length")
            msglen = int.from_bytes(raw_msglen, byteorder='big')
            # Read the message data
            message = self._recvall(client_socket, msglen).decode('utf-8')
            if message:
                data = json.loads(message)
                # A new user connected to me will ask for the other members
                if 'request' in data and data['request'] == 'peers':
                    self._send_peers_list(client_socket)
                # Eventually I'll get a response containing all the users present in the group chat
                # Each user is represented as "ip:port:name"
                elif 'response' in data and data['response'] == 'peers':
                    known_users = [f"{key.getpeername()[0] if key.getpeername()[0] != '127.0.0.1' else self.address}:{self.peers[key][0]}" for key in self.peers]
                    self.peers[client_socket] = [int(data['user'].split(':')[1]), data['user'].split(':')[2]] # I am already connected to the user, so I just update its record with their name
                    for peer in data['peers']:
                        if f"{peer.split(':')[0]}:{peer.split(':')[1]}" not in known_users: # I don't want to connect to the same user twice
                            sk = self._connect_to_peer(peer)
                            if sk is not None:
                                sk.setblocking(False)
                                self.selector.register(sk, selectors.EVENT_READ, self._handle_peer)
                                self.peers[sk] = [int(peer.split(':')[1]), peer.split(':')[2]] # If I connected successfully to the other peer it gets added to the dictionary
                # Message to show a new user in the group chat
                elif 'new_peer' in data and 'port' in data:
                    self.peers[client_socket] = [data['port'], data['new_peer']]
                    print(f"{data['new_peer']} has joined the chat.")
                # Message to show that a user has left the chat
                elif 'disconnect' in data and data['disconnect'] == 'exit':
                    self._remove_peer(client_socket)
                # A simple message to display
                else:
                    self._display_message(message)
        except ConnectionResetError as e:
            # The connection with the peer has closed unexpectedly
            self._remove_peer(client_socket)
        except Exception as e:
            pass

    def _recvall(self, client_socket, n):
        data = bytearray()
        # Loop until we have received the number of bytes we expect
        while len(data) < n:
            packet = client_socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def _display_message(self, message):
        try:
            data = json.loads(message)
            print(f"{data['name']} [{data['time']}]\n - {data['message']}")
        except:
            print("Received malformed message")

    def _broadcast(self, message):
        # Send the message to all the known peers
        for peer in self.peers.keys():
            try:
                peer.send(self._compose_message(message))
            except:
                # If the connection is closed, remove the peer from the list
                self._remove_peer(peer)

    def _connect_to_known_users(self, known_users):
        # Connect to the known users and ask for the list of peers
        connections = []
        for known_user in known_users:
            known_user_socket = self._connect_to_peer(known_user)
            if known_user_socket is not None:
                connections.append(known_user_socket)
                known_user_socket.setblocking(False)
                self.selector.register(known_user_socket, selectors.EVENT_READ, self._handle_peer)
        if len(connections) == 0:
            print("\nAll connections have failed, starting a new group chat\n")
        else:
            for socket in connections:
                socket.send(self._compose_message(json.dumps({'request': 'peers'})))

    def _send_peers_list(self, client_socket):
        # Send the list of peers to the client, including myself
        peers_list = [f"{key.getpeername()[0] if key.getpeername()[0] != '127.0.0.1' else self.address}:{self.peers[key][0]}:{self.peers[key][1]}" 
                      for key in self.peers if key != client_socket]
        user = (f"{self.address}:{self.port}:{self.name}")
        client_socket.send(self._compose_message(json.dumps({'response': 'peers', 'peers': peers_list, "user" : user})))

    def _connect_to_peer(self, peer):
        info = peer.split(':') #Contains the address, the port and optionally the name of the peer
        port = int(info[1])
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_socket.connect((info[0], port))
            self.peers[peer_socket] = [port, ""] # The name will be added afterwards
            peer_socket.send(self._compose_message(json.dumps({'new_peer': self.name, 'port': self.port})))
            return peer_socket
        except Exception as e:
            print(f"Failed to connect to {info[0]}:{port}")
            return None

    # Adds the length of the message to the message itself and adds encoding
    def _compose_message(self, message):
        message = message.encode('utf-8')
        length = len(message)
        return length.to_bytes(4, byteorder='big') + message

    def send_message(self, message):
        if not self.peers:
            print("No peers to send the message to.")
            return
        if message.strip() == "":
            print("Cannot send an empty message.")
            return
        clock_time = time.strftime('%H:%M:%S', time.localtime())
        date = time.strftime('%d-%m-%Y', time.localtime()) # May not be necessary
        message_data = json.dumps({'name': self.name, 'message': message, 'time': clock_time, 'date': date})
        self._broadcast(message_data)

    def disconnect(self):
        print('Disconnecting from the chat...')
        self.server_socket.close()
        if self.peers:
            for peer in self.peers:
                peer.send(self._compose_message(json.dumps({'disconnect': 'exit'})))
                peer.close()
        self.is_online = False
        self.selector.close()

    def _remove_peer(self, peer_socket):
        try:
            peer_socket.close()
        except:
            pass
        print(f"{self.peers[peer_socket][1]} has left the chat.")
        self.selector.unregister(peer_socket)
        del self.peers[peer_socket]


def check_arguments(args, own_address):
    # check if there are enough arguments
    if len(args) < 2:
        print("Usages:\n- poetry run python snippets/lab3/exercise_tcp_group_chat.py <port> [address1:port1 address2:port2 ...]")
        print("- python exercise_tcp_group_chat.py <port> [address1:port1 address2:port2 ...]\n")
        return False
    # check if the port number is valid
    if not args[1].isdigit() or int(args[1]) not in range(0, 65536):
        print("Invalid port number.")
        return False
    # check if the addresses are valid
    if len(args) > 2:
        peers = args[2:]
        for peer in peers:
            address, port = peer.split(':')
            if not is_valid_address(address, port, own_address, int(args[1])):
                print(f"Invalid address: {address}:{port}")
                return False
    return True

def is_valid_address(address, port, own_address, own_port):
    try:
        if address != 'localhost':
            ip = ipaddress.ip_address(address)
            
        port = int(port)
        
        if port not in range(0, 65536):
            return False
        
        # Cannot connect to myself
        if (address == own_address or address=="localhost" or address=="127.0.0.1") and port == own_port:
            return False
        
        return True
    
    except ValueError:
        return False
    
def translate_addresses(addresses, ip):
    translated_list = []
    for address in addresses:
        if 'localhost' in address:
            address.replace('localhost', ip)
        elif '127.0.0.1' in address:
            address.replace('127.0.0.1', ip)
        translated_list.append(address)
    return translated_list


if __name__ == "__main__":
        
    local_chat = False
    
    address = socket.gethostbyname(socket.gethostname()) # Gets the local IP address
    if address == '127.0.0.1':
        local_chat = True
        print("Cannot get the local IP address.\nCan join only chats on this device.\n")
        
    
    if not check_arguments(sys.argv, address):
        sys.exit(1)

    name = input("Enter your name: ")
    port = int(sys.argv[1])
    known_users = sys.argv[2:]
    if not local_chat:
        known_users = translate_addresses(known_users, address)

    try:
        user = TCPChatUser(name, address, port, known_users)
    except OSError as e:
        print("Failed to start the chat. Make sure the port is not in use.")
        sys.exit(1)
        
    if not local_chat:
        print(f"Your local IP address is: [{address}]")
    print("Welcome to the chat! Type your message and press Enter to send it.")
    print("Type 'exit' to leave the chat.\n")

    try:
        while True:
            message = input()
            if message == 'exit':
                user.disconnect()
                break
            user.send_message(message)
    except KeyboardInterrupt:
        print("\nCtrl+C interrupt detected.")
        user.disconnect()
    
    sys.exit(0)
