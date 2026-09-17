from snippets.lab3 import *
import sys
import signal

EXIT_MESSAGE = "<LEAVES THE CHAT>"


class GroupChatPeer:
    def __init__(self, port, initial_peers=None):
        self.port = port
        self.connections = {}  # dict of address -> Connection
        self.username = None

        # Start server to accept incoming connections
        self.server = Server(port, self.on_server_event)

        # Connect to initial peers (passed via command line)
        if initial_peers:
            for peer_addr in initial_peers:
                self.connect_to_peer(peer_addr)

    def connect_to_peer(self, peer_address):
        """Initiate connection to a peer"""
        try:
            peer_addr = address(*peer_address)
            # Avoid connecting to ourselves
            if peer_addr[1] == self.port and peer_addr[0] in ['127.0.0.1', 'localhost', '0.0.0.0']:
                return
            # Avoid duplicate connections
            if peer_addr in self.connections:
                return

            connection = Client(peer_addr, self.on_connection_event)
            self.connections[peer_addr] = connection
            print(f"# Connected to peer at {peer_addr}")
        except Exception as e:
            print(f"# Failed to connect to {peer_address}: {e}")


    def on_server_event(self, event, connection, address_tuple, error):
        """Handle server events (new incoming connections)"""
        match event:
            case 'listen':
                print(f"# Listening on {address_tuple[1]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"# Incoming connection from {address_tuple}")
                connection.callback = self.on_connection_event
                self.connections[address_tuple] = connection
            case 'stop':
                print(f"# Stopped listening for connections")
            case 'error':
                print(f"# Server error: {error}")

    def on_connection_event(self, event, payload, connection, error):
        """Handle connection events (messages, errors, closures)"""
        match event:
            case 'message':
                # Check if it's an exit message
                if EXIT_MESSAGE in payload:
                    print(payload)
                    # Mark connection as gracefully closing to avoid error messages
                    connection._graceful_exit = True
                # Regular message
                else:
                    print(payload)
            case 'close':
                # Remove closed connection
                addr = connection.remote_address
                if addr in self.connections:
                    del self.connections[addr]
                    # Only print if not a graceful exit
                    if not hasattr(connection, '_graceful_exit') or not connection._graceful_exit:
                        print(f"# Connection with {addr} closed ({len(self.connections)} peers remaining)")
            case 'error':
                # Only print error if not a graceful exit or a connection reset
                addr = connection.remote_address
                # WinError 10054 (connection reset) is normal when peer closes, so ignore it
                is_connection_reset = (isinstance(error, OSError) and
                                      (error.errno == 10054 or  # Windows
                                       error.errno == 104))     # Linux
                is_graceful = hasattr(connection, '_graceful_exit') and connection._graceful_exit

                if not is_graceful and not is_connection_reset:
                    print(f"# Connection error: {error}")

                # Clean up connection on error
                if addr in self.connections:
                    del self.connections[addr]

    def broadcast(self, msg):
        """Send message to all connected peers"""
        if not msg.strip():
            return

        formatted_msg = message(msg.strip(), self.username)
        disconnected = []

        for addr, conn in self.connections.items():
            try:
                if not conn.closed:
                    conn.send(formatted_msg)
                else:
                    disconnected.append(addr)
            except Exception as e:
                print(f"# Failed to send to {addr}: {e}")
                disconnected.append(addr)

        # Clean up disconnected peers
        for addr in disconnected:
            if addr in self.connections:
                del self.connections[addr]

    def send_exit_message(self):
        """Send exit message to all peers before closing"""
        if self.username:
            exit_msg = message(EXIT_MESSAGE, self.username)
            disconnected = []
            for addr, conn in self.connections.items():
                try:
                    if not conn.closed:
                        conn.send(exit_msg)
                except Exception as e:
                    print(f"# Failed to send exit message to {addr}: {e}")
                    disconnected.append(addr)
            # Clean up disconnected peers
            for addr in disconnected:
                if addr in self.connections:
                    del self.connections[addr]

    def close(self):
        """Close all connections and server"""
        import time
        self.send_exit_message()
        # Give peers time to receive the exit message before closing
        time.sleep(0.1)
        # Create a copy of connections to avoid RuntimeError if dict changes during iteration
        connections_to_close = list(self.connections.values())
        for conn in connections_to_close:
            if not conn.closed:
                conn.close()
        self.server.close()


if __name__ == '__main__':
    port = int(sys.argv[1])
    initial_peers = [address(peer) for peer in sys.argv[2:]] if len(sys.argv) > 2 else []

    peer = GroupChatPeer(port, initial_peers)

    def handle_termination(signum, frame):
        """Handle forced termination signals."""
        print("\n# Forced termination detected. Shutting down...")
        peer.close()
        sys.exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_termination)
    signal.signal(signal.SIGINT, handle_termination)

    peer.username = input('Enter your username to start the chat:\n')
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

    while True:
        try:
            content = input()
            peer.broadcast(content)
        except (EOFError, KeyboardInterrupt):
            print("\n# Shutting down...")
            peer.close()
            break

    exit(0)