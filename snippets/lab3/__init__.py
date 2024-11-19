from snippets.lab2 import *
import threading

from functools import *


# Uncomment this line to observe timeout errors more often.
# Beware: short timeouts can make demonstrations more difficult to follow.
# socket.setdefaulttimeout(5) # set default timeout for blocking operations to 5 seconds


class Connection:
    def __init__(self, socket: socket.socket, id: str = None, remote_welcoming_address: tuple[str, int] = None, callback=None):
        self._close_lock = threading.Lock()
        
        self.id = id
        self.remote_welcoming_address = remote_welcoming_address

        self.__socket = socket
        self.local_address = self.__socket.getsockname()
        self.remote_address = self.__socket.getpeername()
        self.__notify_closed = False
        self.__callback = callback
        self.__receiver_thread = threading.Thread(target=self.__handle_incoming_messages, daemon=True)
        if self.__callback:
            self.__receiver_thread.start()

    @property
    def callback(self):
        return self.__callback or (lambda *_: None)
    
    @callback.setter
    def callback(self, value):
        if self.__callback:
            raise ValueError("Callback can only be set once")
        self.__callback = value
        if value:
            self.__receiver_thread.start()

    @property
    def closed(self):
        return self.__socket._closed
    
    def send(self, message):
        if not isinstance(message, bytes):
            message = message.encode()
            message = int.to_bytes(len(message), 2, 'big') + message
        self.__socket.sendall(message)

    def receive(self):
        length = int.from_bytes(self.__socket.recv(2), 'big')
        if length == 0:
            return None
        return self.__socket.recv(length).decode()
    
    def close(self):
        with self._close_lock:
            if not self.__notify_closed:
                self.__socket.close()
                self.on_event('close')
                self.__notify_closed = True

    def __handle_incoming_messages(self):
        try:
            while not self.closed:
                message = self.receive()
                if message is None:
                    break
                self.on_event('message', message)
        except Exception as e:
            if self.closed and isinstance(e, OSError):
                return # silently ignore error, because this is simply the socket being closed locally
            self.on_event('error', error=e)
        finally:
            self.close()

    def on_event(self, event: str, payload: str=None, connection: 'Connection'=None, error: Exception=None):
        if connection is None:
            connection = self
        self.callback(event, payload, connection, error)


class Client(Connection):
    def __init__(self, server_address, callback=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(address(port=0))
        sock.connect(address(*server_address))
        super().__init__(sock, callback)


class Server:
    def __init__(self, port, callback=None):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(address(port=port))
        self.__listener_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True)
        self.__callback = callback
        if self.__callback:
            self.__listener_thread.start()

    @property
    def callback(self):
        return self.__callback or (lambda *_: None)
    
    @callback.setter
    def callback(self, value):
        if self.__callback:
            raise ValueError("Callback can only be set once")
        self.__callback = value
        if value:
            self.__listener_thread.start()
    
    def __handle_incoming_connections(self):
        self.__socket.listen()
        self.on_event('listen', address=self.__socket.getsockname())
        try:
            while not self.__socket._closed:
                socket, address = self.__socket.accept()
                connection = Connection(socket)
                self.on_event('connect', connection, address)
        except ConnectionAbortedError as e:
            pass # silently ignore error, because this is simply the socket being closed locally
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')

    def on_event(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None):
        self.__callback(event, connection, address, error)

    def close(self):
        self.__socket.close()
        


#################################


def message(text: str, sender: str, timestamp: datetime=None):
    if timestamp is None:
        timestamp = datetime.now()
    return f"[{timestamp.isoformat()}] {sender}:\n\t{text}"






class Peer:
    def __init__(self, id: str, port: int = 0, bootstrapping_peer: tuple[str, int] = None, callback = None, is_bootstraping: bool = False, bootstrap_port = None, bootstrap_callback = None):

        self.id = id

        self.bootstrapping_peer = bootstrapping_peer
        self.connections: list[Connection] = [] 
        self.is_bootstraping = is_bootstraping


        self._welcoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self._welcoming_socket.bind(address(port=port))
        self._welcoming_thread = threading.Thread(target=self.__handle_incoming_connections, daemon=True)

        self.__callback = callback
        if self.__callback:
            self._welcoming_thread.start()
        
        #if the peer is a bootstraping peer, we need to create a socket to listen for incoming connections
        if self.is_bootstraping:
            self._bootstrap_callback = bootstrap_callback


            self._bootstrap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._bootstrap_socket.bind(address(port=int(bootstrap_port)))

            self._bootstrap_thread = threading.Thread(target=self.__handle_incoming_init_connections, daemon=True)
            
            self._bootstrap_thread.start()


    @property
    def closed(self):
        return self._welcoming_socket._closed
    

    def send_all(self, msg: str):
        for conn in self.connections:
            conn.send(message(msg, self.id))
    
    
    def close(self):

        if self.closed:
            return
    
        
        #then close the welcoming socket
        self._welcoming_socket.close()
        
        #if the peer is a bootstraping peer,  close the bootstraping socket and wait for the thread to join
        if self.is_bootstraping:
            self._bootstrap_socket.close()
            self._bootstrap_thread.join()

        #creates a shallow copy of the connections (it's possible that the connection callback will remove a connection from the list first)
        for conn in list(self.connections):
            #the connection could already be closed from the receinving side connection, if so, we don't need to close it again
            conn.close()
                
        
        self._welcoming_thread.join()


    def __handle_incoming_init_connections(self):
        try:
            self._bootstrap_socket.listen()
            self.on_bootstrap_event('listen', address=self._bootstrap_socket.getsockname())
            while not self.closed:
                socket, address = self._bootstrap_socket.accept()
                self.on_bootstrap_event('connect_ingoing', address)
                self._send_peers_list(socket)
        except ConnectionAbortedError as e:
            pass 
        except Exception as e:
            self.on_bootstrap_event('error', error=e)
        finally:
            self.on_bootstrap_event('stop')
        

    
    def __handle_incoming_connections(self):
        try:
            self._welcoming_socket.listen()
            self.on_event('listen', address=self._welcoming_socket.getsockname())
            while not self.closed:
                socket, addr = self._welcoming_socket.accept()



                data_size = int.from_bytes(socket.recv(4), byteorder="big")
                data = socket.recv(data_size).decode()  
                username, ip, port = data.split('|')

                
                connection = Connection(socket, id=username, remote_welcoming_address= address(ip, int(port)))
                self.connections.append(connection)
                self.on_event('connect_ingoing', connection, addr)
        except ConnectionAbortedError as e:
            pass 
        except Exception as e:
            self.on_event('error', error=e)
        finally:
            self.on_event('stop')


    def on_event(self, event: str, connection: Connection=None, address: tuple=None, error: Exception=None):
        self.__callback(event, connection, self.connections, address, error)

    def on_bootstrap_event(self, event: str, address: tuple=None, error: Exception=None, peers_list: list[tuple[str, int]] = None):
        self._bootstrap_callback(event, address, error, peers_list)



    def __connect_to(self, peer: tuple[str, int], remote_username, callback, timeout = 5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(address(port=0))
        sock.settimeout(timeout)

        #if the peer welcoming address is waiting from all of its interfaces, we need to change it to localhost
        #the solution is not perfect, but it's a simplification for the lab
        if peer[0] == '0.0.0.0':
            peer = ('localhost', peer[1])


        try:
            
            sock.connect(peer)
            sock.settimeout(None)

            local_username = self.id 
            local_ip, local_port = self._welcoming_socket.getsockname() 
            data_string = f"{local_username}|{local_ip}|{local_port}"
            data = data_string.encode()


            sock.sendall(len(data).to_bytes(4, byteorder="big"))
            sock.sendall(data)
            

            connection = Connection(sock, id=remote_username, remote_welcoming_address=peer)
            self.connections.append(connection)
            self.on_event('connect_outgoing', connection, peer) 
        except TimeoutError as e:
            self.on_event('error', error= "Attempt to connect with {}:{} failed with a timeout".format(peer[0], peer[1]))
            #no need to remove the connection, it is not added to the list in case of timeout
            sock.close()

    def _send_peers_list(self, sender: socket.socket):
        peers_list = [(conn.id, conn.remote_welcoming_address[0], conn.remote_welcoming_address[1]) for conn in self.connections]
        peers_list.append((self.id, self._welcoming_socket.getsockname()[0], self._welcoming_socket.getsockname()[1]))


        data_string = '\n'.join([f"{user}|{ip}|{port}" for user, ip, port in peers_list])
        data = data_string.encode()

        try:
            sender.sendall(len(data).to_bytes(4, byteorder="big"))
            sender.sendall(data)
            self.on_bootstrap_event('send_peers', address=sender.getpeername(), peers_list=peers_list)
        except Exception as e:
            self.on_bootstrap_event('error', error="[Peer sending failed] " + e)
        finally:
            self.on_bootstrap_event('close', address=sender.getpeername())
            sender.close()
            




    def _receive_peers_list(self, remote_peer: tuple[str, int]):

        try:

            socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_conn.connect(remote_peer)

            data_size = int.from_bytes(socket_conn.recv(4), byteorder='big')


            data = b""
            while len(data) < data_size:
                packet = socket_conn.recv(1024)
                if not packet:
                    break
                data += packet


            data_string = data.decode()
            peers_list = []
            for line in data_string.split('\n'):
                if line.strip():  # Avoid empty lines
                    user, ip, port = line.split('|')
                    peers_list.append((user, ip, int(port)))

            return peers_list
        except Exception as e:
            raise ValueError("Bootstrapping peer was not reachable or the retrieval failed, retry or try to connect to another bootstrap address")
        finally:
            socket_conn.close()  
    

    def init_connect(self, peers_connection_callback = None):


        if self.bootstrapping_peer is None:
            return 

        #if the callback is set, we need to pass as a partial function the connections list of the peer
        if peers_connection_callback is not None:
            peers_connection_callback = partial(peers_connection_callback, connections = self.connections)
        

        peers_list = self._receive_peers_list(address(self.bootstrapping_peer)) 
        


        connect_threads = []
        for username, ip, port in peers_list:
            t = threading.Thread(target=self.__connect_to, args = (address(ip, port), username, peers_connection_callback), daemon=True)
            t.start()
            connect_threads.append(t)
        
        for t in connect_threads:
            t.join()
        

        


    


        
        