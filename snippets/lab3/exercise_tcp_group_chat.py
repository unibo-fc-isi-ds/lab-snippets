from snippets.lab3 import *
from snippets.lab2 import message, address
import sys


class Peer:
    """
    A P2P peer that can connect to other peers and broadcast messages.
    Peers memorize any peer they receive a message from and forward subsequent messages to them.
    """
    def __init__(self, port, initial_peers=None):
        self.port = port
        self.known_peers = set()
        if initial_peers:
            for peer_addr in initial_peers:
                self.known_peers.add(address(peer_addr))
        
        # Server to accept incoming connections
        self.server = Server(port, self.__on_server_event)
        
        # Active connections to other peers (outgoing)
        self.outgoing_connections = {}
        
        # Active connections from other peers (incoming)
        self.incoming_connections = {}
        
        self.running = True

    def __on_server_event(self, event, connection, addr, error):
        """Handle server events (incoming connections)"""
        match event:
            case 'listen':
                print(f"Peer listening on port {self.port} at {', '.join(local_ips())}")
            case 'connect':
                print(f"New incoming connection from: {addr}")
                connection.callback = self.__on_incoming_message
                self.incoming_connections[addr] = connection
                # Memorize this peer
                self.known_peers.add(addr)
            case 'error':
                print(f"Server error: {error}")
            case 'stop':
                print("Server stopped listening")

    def __on_incoming_message(self, event, payload, connection, error):
        """Handle messages from incoming connections"""
        match event:
            case 'message':
                print(payload)
                # Memorize the sender
                self.known_peers.add(connection.remote_address)
            case 'close':
                print(f"Connection with peer {connection.remote_address} closed")
                if connection.remote_address in self.incoming_connections:
                    del self.incoming_connections[connection.remote_address]
            case 'error':
                print(f"Connection error: {error}")

    def __connect_to_peer(self, peer_addr):
        """Connect to a peer (outgoing connection)"""
        if peer_addr in self.outgoing_connections:
            return self.outgoing_connections[peer_addr]
        
        try:
            client = Client(peer_addr, self.__on_outgoing_message)
            self.outgoing_connections[peer_addr] = client
            self.known_peers.add(peer_addr)
            print(f"Connected to peer {peer_addr}")
            return client
        except Exception as e:
            print(f"Failed to connect to {peer_addr}: {e}")
            return None

    def __on_outgoing_message(self, event, payload, connection, error):
        """Handle events from outgoing connections"""
        match event:
            case 'close':
                print(f"Connection to peer {connection.remote_address} closed")
                if connection.remote_address in self.outgoing_connections:
                    del self.outgoing_connections[connection.remote_address]
            case 'error':
                print(f"Connection error: {error}")

    def send_to_all(self, msg, sender):
        """Broadcast a message to all known peers"""
        if not msg:
            print("Empty message, not sent")
            return
        
        formatted_msg = message(msg.strip(), sender)
        
        # Track which peers we've sent to (to avoid duplicates)
        sent_to = set()
        
        # Send to all outgoing connections
        disconnected_peers = []
        for peer_addr, conn in list(self.outgoing_connections.items()):
            try:
                if not conn.closed:
                    conn.send(formatted_msg)
                    sent_to.add(peer_addr)
                else:
                    disconnected_peers.append(peer_addr)
            except Exception as e:
                print(f"Error sending to {peer_addr}: {e}")
                disconnected_peers.append(peer_addr)
        
        # Remove disconnected peers
        for peer_addr in disconnected_peers:
            if peer_addr in self.outgoing_connections:
                del self.outgoing_connections[peer_addr]
        
        # Send to all incoming connections (that we haven't already sent to)
        disconnected_incoming = []
        for peer_addr, conn in list(self.incoming_connections.items()):
            if peer_addr not in sent_to:
                try:
                    if not conn.closed:
                        conn.send(formatted_msg)
                        sent_to.add(peer_addr)
                    else:
                        disconnected_incoming.append(peer_addr)
                except Exception as e:
                    print(f"Error sending to {peer_addr}: {e}")
                    disconnected_incoming.append(peer_addr)
        
        # Remove disconnected incoming peers
        for peer_addr in disconnected_incoming:
            if peer_addr in self.incoming_connections:
                del self.incoming_connections[peer_addr]
        
        # Try to connect to known peers we haven't connected to yet
        # (only if we don't already have any connection to them)
        for peer_addr in list(self.known_peers):
            # Skip if we already have a connection (incoming or outgoing)
            if peer_addr in self.outgoing_connections or peer_addr in self.incoming_connections:
                continue
            # Don't connect to ourselves
            local_addr = address()
            if peer_addr[1] == self.port or peer_addr == (local_addr[0], self.port):
                continue
            self.__connect_to_peer(peer_addr)

    def close(self):
        """Close all connections and stop the server"""
        self.running = False
        for conn in list(self.outgoing_connections.values()):
            try:
                conn.close()
            except:
                pass
        self.outgoing_connections.clear()
        self.incoming_connections.clear()
        self.server.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m snippets.lab3.exercise_tcp_group_chat <port> [peer1] [peer2] ...")
        print("Example: python -m snippets.lab3.exercise_tcp_group_chat 8080 127.0.0.1:8081 127.0.0.1:8082")
        sys.exit(1)
    
    port = int(sys.argv[1])
    initial_peers = sys.argv[2:] if len(sys.argv) > 2 else []
    
    peer = Peer(port, initial_peers)
    
    # Connect to initial peers
    for peer_addr_str in initial_peers:
        peer_addr = address(peer_addr_str)
        peer._Peer__connect_to_peer(peer_addr)
    
    username = input('Enter your username to start the chat:\n')
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
    
    try:
        while True:
            content = input()
            peer.send_to_all(content, username)
    except (EOFError, KeyboardInterrupt):
        peer.close()
        print("\nPeer closed")

