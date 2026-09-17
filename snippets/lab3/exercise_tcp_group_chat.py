"""
@author Daniele Romanella
TCP Group Chat Exercise with Message Forwarding
A.Y. 2025/2026 - Distributed Systems

Group chat using TCP sockets with message forwarding capabilities.
Every peer is both a server (accepts new peers) and a client (connects itself to other peers) at the same time.

Features:
- Message forwarding: messages are propagated through the network
- Loop prevention: SHA256 hash-based deduplication
- Limited memory: only last 10 message hashes are stored
"""

from snippets.lab3 import Client, Server
from snippets.lab2 import message, address, local_ips
import threading
import sys
import hashlib
from collections import deque

MAX_HASH_TO_HANDLE = 10


def _compute_hash(msg):
    """
    Compute SHA256 hash of a message.

    Args:
        msg: the message string

    Returns:
        hexadecimal hash string
    """
    return hashlib.sha256(msg.encode('utf-8')).hexdigest()


class TCPGroupPeer:
    """
    A peer participating in a TCP group chat with message forwarding.

    Features:
    - Listens for incoming connections (as server)
    - Connects to known peers (as client)
    - Maintains a list of active connections
    - Broadcasts messages to all connected peers
    - Forwards received messages to other peers (flooding with loop prevention)
    - Uses SHA256 hash to track seen messages and prevent loops
    """

    def __init__(self, port, peers=None, username=None):
        """
        Initialize the peer.

        Args:
            port: port to listen for incoming connections
            peers: list of tuples (ip, port) of peers to connect to
            username: username (optional, will be requested later if None)
        """
        self.port = port
        self.username = username
        self.connections = {}  # {(ip, port): Connection}
        self.lock = threading.Lock()  # For thread-safe access to connections

        # Message deduplication: store hashes of last 10 messages
        self.seen_hashes = deque(maxlen=MAX_HASH_TO_HANDLE)  # Automatically removes oldest when > 10
        self.hash_lock = threading.Lock()  # Thread-safe access to seen_hashes

        # Start the server to accept incoming connections
        self.server = Server(port=port, callback=self._on_server_event)

        print(f"# Server listening on port {port}")
        print(f"# Local IP addresses: {', '.join(local_ips())}")

        # Connect to initial peers (if provided)
        if peers:
            for peer_addr in peers:
                self._connect_to_peer(peer_addr)

    def _has_seen(self, msg_hash):
        """
        Check if a message hash has been seen before.

        Args:
            msg_hash: SHA256 hash of the message

        Returns:
            True if hash is in cache, False otherwise
        """
        with self.hash_lock:
            return msg_hash in self.seen_hashes

    def _mark_as_seen(self, msg_hash):
        """
        Mark a message as seen by adding its hash to the cache.

        Args:
            msg_hash: SHA256 hash of the message
        """
        with self.hash_lock:
            if msg_hash not in self.seen_hashes:
                self.seen_hashes.append(msg_hash)

    def _connect_to_peer(self, peer_address):
        """
        Opens a connection to a remote peer.

        Args:
            peer_address: tuple (ip, port) of the peer
        """
        try:
            # Create a Client that connects to the remote peer
            client = Client(server_address=peer_address, callback=self._on_message_event)

            # Save the connection in the dictionary (thread-safe)
            with self.lock:
                self.connections[peer_address] = client

            print(f"# Connection opened to {peer_address}")

        except Exception as e:
            print(f"# Connection error to {peer_address}: {e}")

    def _on_server_event(self, event, connection, address, error):
        """
        Callback invoked by Server when events occur.

        Possible events:
        - 'listen': the server has started listening
        - 'connect': new incoming connection accepted
        - 'stop': the server has stopped listening
        - 'error': error during connection handling
        """
        match event:
            case 'listen':
                print(f"# Server listening on {address}")

            case 'connect':
                # Check if connection already exists with this peer
                with self.lock:
                    if address not in self.connections:
                        # Save the new connection
                        self.connections[address] = connection
                        # Set the callback for messages
                        connection.callback = self._on_message_event
                        print(f"# New incoming connection from {address}")
                    else:
                        print(f"# Duplicate connection from {address}, ignored")

            case 'stop':
                print("# Server stopped")

            case 'error':
                print(f"# Server error: {error}")

    def _on_message_event(self, event, payload, connection, error):
        """
        Callback invoked by Connection when messages or events arrive.

        Possible events:
        - 'message': new message received
        - 'close': the connection has been closed
        - 'error': error during communication
        """
        match event:
            case 'message':
                # Compute hash of the received message
                msg_hash = _compute_hash(payload)

                # Check if we've already seen this message
                if self._has_seen(msg_hash):
                    return  # Don't print or forward duplicate messages

                # Mark as seen BEFORE printing and forwarding
                self._mark_as_seen(msg_hash)

                # Print the received message
                print(payload)

                # Forward the message to all other peers (except sender)
                self._forward_message(payload, exclude_connection=connection)

            case 'close':
                # Remove the connection from the list
                with self.lock:
                    # Find which address corresponds to this connection
                    for addr, conn in list(self.connections.items()):
                        if conn == connection:
                            del self.connections[addr]
                            print(f"# Connection closed with {addr}")
                            break

            case 'error':
                print(f"# Connection error: {error}")

    def _forward_message(self, msg, exclude_connection=None):
        """
        Forward a message to all connected peers except one.

        This implements message flooding with loop prevention.
        Used when a message is received from a peer and needs to be
        propagated to the rest of the network.

        Args:
            msg: the formatted message to forward
            exclude_connection: Connection object to exclude (usually the sender)
        """
        with self.lock:
            forwarded_count = 0
            for addr, conn in list(self.connections.items()):
                # Skip the connection we received the message from
                if conn == exclude_connection:
                    continue

                try:
                    conn.send(msg)
                    forwarded_count += 1
                except Exception as e:
                    print(f"# Error forwarding to {addr}: {e}")

    def broadcast(self, text, sender):
        """
        Sends a message to all connected peers.

        This is used for locally generated messages (from user input).
        The message is marked as seen and sent to all peers.

        Args:
            text: message content
            sender: sender's username
        """
        # Format the message with timestamp
        msg = message(text, sender)

        # Compute hash and mark as seen BEFORE sending
        # This prevents the message from being forwarded back if it somehow loops
        msg_hash = _compute_hash(msg)
        self._mark_as_seen(msg_hash)

        # Send to all active connections
        with self.lock:
            sent_count = 0
            for addr, conn in list(self.connections.items()):
                try:
                    conn.send(msg)
                    sent_count += 1
                except Exception as e:
                    print(f"# Error sending to {addr}: {e}")

            if sent_count > 0:
                print(f"# Message sent to {sent_count} peer(s)")
            else:
                print("# Warning: no peers connected, message not sent")

    def close(self):
        """Closes all connections and the server."""
        print("# Closing...")

        # Close all connections
        with self.lock:
            for conn in self.connections.values():
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()

        # Close the server
        try:
            self.server.close()
        except:
            pass

        print("# Peer closed")


def main():
    """Main function to run the peer."""

    # Argument parsing: PORT [PEER1_IP:PORT] [PEER2_IP:PORT] ...
    if len(sys.argv) < 2:
        print("Usage: python exercise_tcp_group_chat.py PORT [PEER1 PEER2 ...]")
        print("Example: python exercise_tcp_group_chat.py 8080")
        print("Example: python exercise_tcp_group_chat.py 8081 localhost:8080")
        print("\nNote: With message forwarding, peers don't need to be fully connected.")
        print("      Messages will be propagated through the network automatically.")
        sys.exit(1)

    port = int(sys.argv[1])
    peers = [address(p) for p in sys.argv[2:]] if len(sys.argv) > 2 else []

    # Create the peer
    peer = TCPGroupPeer(port=port, peers=peers)

    # Request username
    username = input("Enter your username: ")
    peer.username = username

    print("\nType your messages and press Enter to send them.")
    print("Press Ctrl+D (Unix) or Ctrl+Z then Enter (Windows) to exit.\n")

    # Main loop: read messages from user and send them
    try:
        while True:
            try:
                content = input()
                if content.strip():  # Send only non-empty messages
                    peer.broadcast(content, username)
            except EOFError:
                # Ctrl+D pressed
                break
    except KeyboardInterrupt:
        # Ctrl+C pressed
        pass
    finally:
        # Graceful shutdown
        peer.close()


if __name__ == "__main__":
    main()
