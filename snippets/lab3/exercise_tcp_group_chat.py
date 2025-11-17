import socket
import threading
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import queue

from snippets.lab3.common import *
from snippets.lab3 import *

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
                client = ClientGroup(chat_room, conn)
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

            client = ClientGroup(chat_room, conn)
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