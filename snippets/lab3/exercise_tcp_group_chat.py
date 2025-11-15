# Python TCP Group Chat - Ported from Go
# Dynamic peer-to-peer chat with message history synchronization
# Each peer acts as both server (listens for connections) and client (connects to other peers)

import socket
import threading
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import queue
from collections import defaultdict

# Constants
CONN_TYPE = "tcp"
CMD_PREFIX = "/"
CMD_JOIN = CMD_PREFIX + "join"
CMD_DIAL = CMD_PREFIX + "dial"
CMD_INIT = CMD_PREFIX + "init"
CMD_LEAVE = CMD_PREFIX + "leave"
CMD_CHATSEND = CMD_PREFIX + "chatS"
CMD_CHATRECEIVE = CMD_PREFIX + "chatR"

# ANSI Color codes
PURPLE_CLR = "\033[35m"
CYAN_CLR = "\033[36m"
WHITE_CLR = "\033[10m"
YELLOW_CLR = "\033[33m"
GREEN_CLR = "\033[32m"
RESET_CLR = "\033[0m"


class Message:
    """Represents a chat message with timestamp and sender"""

    def __init__(self, msg_time: datetime, client_name: str, text: str):
        self.msg_time = msg_time
        self.client_name = client_name
        self.text = text

    def __str__(self) -> str:
        return f"{WHITE_CLR}{self.msg_time.strftime('%H:%M:%S')} - {self.client_name}:{GREEN_CLR} {self.text}\n{RESET_CLR}"

    def to_plain_string(self) -> str:
        """Format message for storage"""
        return f"{WHITE_CLR}{self.msg_time.strftime('%H:%M:%S')} - {self.client_name}:{GREEN_CLR} {self.text}\n{RESET_CLR}"


class Client:
    """Represents a connected peer in the chat room"""

    def __init__(self, chat_room: 'ChatRoom', conn: socket.socket):
        self.name = ""
        self.chat_room = chat_room
        self.incoming = queue.Queue(maxsize=1)
        self.outgoing = queue.Queue()
        self.conn = conn
        self.is_running = True
        self.lock = threading.Lock()

        # Start all listening threads
        self.listen()

    def quit(self):
        """Handle client disconnect"""
        self.is_running = False
        
        # Broadcast leave notification to all other peers before removing
        if self.name:
            leave_msg = f"{CMD_LEAVE} {self.name}\n"
            self.chat_room.broadcast_except(leave_msg, self)
            print(f"{PURPLE_CLR}{self.name} has left the chat{RESET_CLR}")
        else:
            # If name not set, still try to notify
            print(f"{PURPLE_CLR}A peer has left the chat{RESET_CLR}")

        remote_addr = None
        try:
            remote_addr = self.conn.getpeername()
        except:
            pass

        if remote_addr:
            with self.chat_room.lock:
                if remote_addr in self.chat_room.clients:
                    del self.chat_room.clients[remote_addr]

        try:
            self.conn.close()
        except:
            pass

    def read_messages(self):
        """Process incoming messages with command parsing"""
        while self.is_running:
            try:
                message_obj = self.incoming.get(timeout=1)
                if message_obj is None:
                    continue

                text = message_obj.text

                # Default: print regular chat message and forward to other peers
                if not text.startswith(CMD_PREFIX):
                    msg_str = str(message_obj)
                    with self.chat_room.lock:
                        self.chat_room.messages.append(msg_str)
                    print(msg_str, end='')
                    # Forward message to all other peers (excluding sender)
                    # Include sender name in forwarded message so recipients know who sent it
                    if self.name:
                        # Forward with sender name prefix: "sender_name|message"
                        forward_msg = f"{self.name}|{text}\n"
                    else:
                        # If name not set yet, just forward the text
                        forward_msg = text + "\n"
                    self.chat_room.broadcast_except(forward_msg, self)

                # CMD_INIT: Set client name (name of the peer on the other end of this connection)
                elif text.startswith(CMD_INIT):
                    name = text[len(CMD_INIT):].strip()
                    if not self.name:  # Only set if not already set
                        self.name = name
                    # Don't forward - each peer sends their own name directly to each connection
                
                # CMD_LEAVE: Peer has left the chat
                elif text.startswith(CMD_LEAVE):
                    peer_name = text[len(CMD_LEAVE):].strip()
                    print(f"{PURPLE_CLR}{peer_name} has left the chat{RESET_CLR}")
                    # Forward leave message to all other peers (excluding sender)
                    self.chat_room.broadcast_except(text + "\n", self)

                # CMD_CHATSEND: Send chat history to requestor
                elif text.startswith(CMD_CHATSEND):
                    port = text[len(CMD_CHATSEND):].strip()
                    with self.chat_room.lock:
                        for addr, client in self.chat_room.clients.items():
                            if str(addr[1]) == port:
                                try:
                                    messages_json = json.dumps(self.chat_room.messages)
                                    self.outgoing.put(f"{CMD_CHATRECEIVE} {messages_json}\n")
                                except Exception as e:
                                    print(f"Error serializing messages: {e}")
                                break

                # CMD_CHATRECEIVE: Receive and display chat history
                elif text.startswith(CMD_CHATRECEIVE):
                    messages_str = text[len(CMD_CHATRECEIVE):].strip().rstrip('\n')
                    try:
                        messages_list = json.loads(messages_str)
                        with self.chat_room.lock:
                            self.chat_room.messages = messages_list
                        for msg in messages_list:
                            print(msg, end='')
                    except Exception as e:
                        print(f"Error deserializing messages: {e}")

                # CMD_JOIN: New peer joined, broadcast to others
                elif text.startswith(CMD_JOIN):
                    join_msg = text[len(CMD_JOIN):].strip()
                    parts = join_msg.split('|')
                    if len(parts) >= 2:
                        peer_name = parts[1].strip()
                        print(f"{CYAN_CLR}{peer_name} has joined the chat{RESET_CLR}")
                        # Forward join message to all other peers (excluding sender)
                        # Forward the original message text to maintain format
                        self.chat_room.broadcast_except(text + "\n", self)

                # CMD_DIAL: Peer notification to dial another peer
                elif text.startswith(CMD_DIAL):
                    parts = text.split('|')
                    port = parts[0][len(CMD_DIAL):].strip()
                    peer_name = parts[1].strip() if len(parts) > 1 else "Unknown"

                    if port == self.chat_room.conn_port:
                        continue

                    print(f"{CYAN_CLR}{peer_name} has joined the chat{RESET_CLR}")

                    # Check if not already connected
                    # We need to check if we're already connected to a peer listening on this port
                    with self.chat_room.lock:
                        already_connected = False
                        for addr, client in self.chat_room.clients.items():
                            # When we connect OUT to a peer, addr[1] is their listening port
                            # When a peer connects IN to us, addr[1] is their ephemeral port (not listening port)
                            # So we check if the target port matches the remote port (for outgoing connections)
                            remote_port = str(addr[1])
                            if port == remote_port:
                                already_connected = True
                                break
                            
                            # Also check if this is our own port (shouldn't connect to ourselves)
                            if port == self.chat_room.conn_port:
                                already_connected = True
                                break
                        
                        if not already_connected and port != self.chat_room.conn_port:
                            try:
                                new_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                new_conn.connect(('localhost', int(port)))
                                new_client = Client(self.chat_room, new_conn)
                                self.chat_room.join(new_client)
                                # Send our name to the newly connected peer
                                if self.chat_room.point_name:
                                    try:
                                        new_client.outgoing.put(f"{CMD_INIT} {self.chat_room.point_name}\n")
                                    except:
                                        pass
                            except Exception as e:
                                print(f"Error connecting to {port}: {e}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in read_messages: {e}")
                self.quit()
                break

    def write_messages(self):
        """Send outgoing messages to socket"""
        while self.is_running:
            try:
                message = self.outgoing.get(timeout=1)
                if message is None:
                    continue

                self.conn.sendall(message.encode('utf-8'))
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error writing to socket: {e}")
                self.quit()
                break

    def client_read(self):
        """Read from socket and put into incoming queue"""
        while self.is_running:
            try:
                data = self.conn.recv(4096).decode('utf-8')
                if not data:
                    self.quit()
                    break

                # Handle multiple messages separated by newlines
                messages = data.split('\n')
                for msg_text in messages:
                    if msg_text:
                        # Check if message has sender name prefix (format: "sender_name|message")
                        # This happens when a message is forwarded from another peer
                        sender_name = self.name  # Default to connection's name
                        actual_msg = msg_text
                        
                        if '|' in msg_text and not msg_text.startswith(CMD_PREFIX):
                            # Split on first '|' to get sender name and message
                            parts = msg_text.split('|', 1)
                            if len(parts) == 2:
                                sender_name = parts[0].strip()
                                actual_msg = parts[1].strip()
                        
                        message_obj = Message(datetime.now(), sender_name, actual_msg)
                        try:
                            self.incoming.put(message_obj, timeout=1)
                        except queue.Full:
                            pass

            except Exception as e:
                print(f"Error reading from socket: {e}")
                self.quit()
                break


    def listen(self):
        """Start all listener threads"""
        threading.Thread(target=self.read_messages, daemon=True).start()
        threading.Thread(target=self.write_messages, daemon=True).start()
        threading.Thread(target=self.client_read, daemon=True).start()
        # Note: client_write (stdin reader) is NOT started here - it's only started once in main()


class ChatRoom:
    """Manages all connected clients and shared chat state"""

    def __init__(self, conn_port: str):
        self.point_name = ""
        self.clients: Dict = {}  # Maps remote_address -> Client
        self.conn_port = conn_port
        self.messages: List[str] = []
        self.lock = threading.Lock()

    def join(self, client: Client):
        """Add a client to the chat room"""
        remote_addr = client.conn.getpeername()
        with self.lock:
            self.clients[remote_addr] = client
            # Send our name to the newly connected peer
            if self.point_name:
                try:
                    client.outgoing.put(f"{CMD_INIT} {self.point_name}\n")
                except:
                    pass

    def broadcast(self, message: str):
        """Send message to all connected clients"""
        with self.lock:
            for client in self.clients.values():
                try:
                    client.outgoing.put(message, timeout=0.1)
                except queue.Full:
                    pass
                except Exception as e:
                    # Client might be disconnected, skip it
                    pass

    def broadcast_except(self, message: str, exclude_client: Client):
        """Send message to all connected clients except the specified one"""
        with self.lock:
            for client in self.clients.values():
                if client == exclude_client:
                    continue
                try:
                    client.outgoing.put(message, timeout=0.1)
                except queue.Full:
                    pass
                except Exception as e:
                    # Client might be disconnected, skip it
                    pass


def start_listener(chat_room: ChatRoom, port: int):
    """Start listening for incoming connections"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(('localhost', port))
        server_socket.listen(5)
        print(f"{PURPLE_CLR}listening on port localhost:{port}{RESET_CLR}")

        while True:
            try:
                conn, addr = server_socket.accept()
                print(f"{CYAN_CLR}New connection from {addr}{RESET_CLR}")
                client = Client(chat_room, conn)
                chat_room.join(client)
                # Send our name to the newly connected peer
                if chat_room.point_name:
                    try:
                        client.outgoing.put(f"{CMD_INIT} {chat_room.point_name}\n")
                    except:
                        pass
            except Exception as e:
                print(f"Error accepting connection: {e}")

    finally:
        server_socket.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python tcp_group_chat.py <port> [server_host:server_port]")
        print("Example: python tcp_group_chat.py 8080 localhost:8081")
        sys.exit(1)

    try:
        conn_port = int(sys.argv[1])
    except ValueError:
        print("Port must be a number")
        sys.exit(1)

    chat_room = ChatRoom(str(conn_port))

    # Start server listener in background thread
    listener_thread = threading.Thread(
        target=start_listener,
        args=(chat_room, conn_port),
        daemon=True
    )
    listener_thread.start()

    # Get username
    print(f"{GREEN_CLR}Enter name: {RESET_CLR}", end='')
    sys.stdout.flush()
    point_name = input().strip()
    chat_room.point_name = point_name

    # Connect to initial peer if provided
    if len(sys.argv) >= 3:
        server_addr = sys.argv[2]
        try:
            host, port = server_addr.split(':')
            port = int(port)

            print(f"{YELLOW_CLR}Connecting to {host}:{port}...{RESET_CLR}")
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((host, port))

            client = Client(chat_room, conn)
            chat_room.join(client)

            # Send our name to the peer we're connecting to
            if point_name:
                client.outgoing.put(f"{CMD_INIT} {point_name}\n")

            # Announce join and request chat history
            join_msg = f"{CMD_JOIN} {CMD_DIAL} {conn_port}|{point_name}\n"
            client.outgoing.put(join_msg)

            history_msg = f"{CMD_CHATSEND} {conn.getsockname()[1]}\n"
            client.outgoing.put(history_msg)

        except Exception as e:
            print(f"Error connecting to server: {e}")

    # Start stdin reader (only once, not per client)
    def stdin_reader():
        """Read stdin and broadcast messages to all peers"""
        # Send init message to all connected clients
        chat_room.broadcast(f"{CMD_INIT} {chat_room.point_name}\n")
        
        while True:
            try:
                user_input = input()
                if not user_input:
                    continue

                # Remove leading slash if present
                if user_input.startswith(CMD_PREFIX):
                    user_input = user_input[1:]

                # Add to local message history
                plain_msg = f"{WHITE_CLR}{datetime.now().strftime('%H:%M:%S')} - {chat_room.point_name}:{GREEN_CLR} {user_input}\n{RESET_CLR}"
                with chat_room.lock:
                    chat_room.messages.append(plain_msg)

                # Broadcast to all peers
                chat_room.broadcast(user_input + "\n")

            except EOFError:
                break
            except Exception as e:
                print(f"Error reading stdin: {e}")
                break

    stdin_thread = threading.Thread(target=stdin_reader, daemon=True)
    stdin_thread.start()

    # Keep main thread alive
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print(f"\n{PURPLE_CLR}Goodbye!{RESET_CLR}")
        sys.exit(0)


if __name__ == "__main__":
    main()