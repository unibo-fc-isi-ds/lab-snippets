import socket
import threading
import sys
import json
import time
import selectors
import re

class ChatUser:
    def __init__(self, name, port, known_users=None):
        self.name = name
        self.port = port
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
        print("Welcome to the chat! Type your message and press Enter to send it.")
        print("Type 'exit' to leave the chat.\n")

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
                raise Exception("Malformed message")
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
                    known_users = [f"{key.getpeername()[0]}:{self.peers[key][0]}" for key in self.peers]
                    self.peers[client_socket] = [int(data['user'].split(':')[1]), data['user'].split(':')[2]] # I am already connected to the user, so I just update its record with their name
                    for peer in data['peers']:
                        if f"{peer.split(':')[0]}:{peer.split(':')[1]}" not in known_users:
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
                else:
                    self._display_message(message)
                    # self._broadcast(message, client_socket)
        except ConnectionResetError as e:
            self._remove_peer(client_socket)
        except Exception as e:
            #print(f"Error: {e}")
            pass

    def _recvall(self, client_socket, n):
        data = bytearray()
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

    def _broadcast(self, message, exclude_socket=None):
        for peer in self.peers.keys():
            if peer != exclude_socket:
                try:
                    peer.send(self._compose_message(message))
                except:
                    self._remove_peer(peer)

    def _connect_to_known_users(self, known_users=None):
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
        peers_list = [f"{key.getpeername()[0]}:{self.peers[key][0]}:{self.peers[key][1]}" for key in self.peers if key != client_socket]
        user = (f"{self.server_socket.getsockname()[0]}:{self.port}:{self.name}")
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

    # Adds the length of the message to the message itself
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


def check_arguments(args):
    # check if there are enough arguments
    if len(args) < 2:
        print("Usage: python simple_tcp_chat_group.py <port> [address1:port1 address2:port2 ...]")
        return False
    # check if the port number is valid
    if not args[1].isdigit() or int(args[1]) not in range(1025, 65536):
        print("Invalid port number.")
        return False
    # check if the addresses are valid
    if len(args) > 2:
        addresses = args[2:]
        for address in addresses:
            if not is_valid_address(address):
                print(f"Invalid address: {address}")
                return False
    return True
            
def is_valid_address(address):
    # Regular expression to match the format "x.x.x.x:y"
    pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$')
    if not pattern.match(address):
        return False

    # Split the address into IP and port
    ip, port = address.split(':')
    port = int(port)

    # Check if port is in the valid range
    if port < 0 or port > 65535:
        return False

    # Check if each part of the IP is in the valid range
    octets = ip.split('.')
    for octet in octets:
        if int(octet) < 0 or int(octet) > 255:
            return False

    return True
    

if __name__ == "__main__":
    
    if not check_arguments(sys.argv):
        sys.exit(1)

    name = input("Enter your name: ")
    port = int(sys.argv[1])
    known_users = sys.argv[2:]

    user = ChatUser(name, port, known_users)

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
