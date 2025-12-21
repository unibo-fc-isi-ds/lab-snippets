from snippets.lab3 import *
import sys

import argparse

def get_msg_str(msg, sender) -> str:
    return message(msg.strip(), sender)

def run(port: int, remote_endpoints: list[tuple[str, int]]):
    username = input('Enter your username to start the chat:\n')
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
    
    server_connections: dict[str, Connection]
    seen_messages = set()
    
    def on_message_server(event, payload, connection, error):
        match event:
            case 'message':
                # Check if we have already fowarded the message
                if payload in seen_messages:
                    return
                seen_messages.add(payload)
                for conn in server_connections.values():
                    if conn.remote_address == connection.remote_address:
                        continue  # Do not echo back to sender
                    conn.send(payload)
                print(payload)
            case 'close':
                print(f"Connection with peer {connection.remote_address} closed")
                del server_connections[connection.remote_address]  # Remove peer
            case 'error':
                print(error)

    # Initial connections
    clients = [Client(addr, on_message_server) for addr in remote_endpoints]
    
    server_connections: dict[str, Connection] = {
        client.remote_address: client for client in clients
    }

    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = on_message_server
                server_connections[address] = connection
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

    server = Server(port, on_new_connection)

    while True:
        try:
            content = input()
            if not content:
                continue  # Empty message, skip
            msg = get_msg_str(content, username)
            for connection in server_connections.values():
                connection.send(msg)
        except (EOFError, KeyboardInterrupt):
            server.close()
            server.join()
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int)
    parser.add_argument("remote_peers", nargs="*", default=[])
    args = parser.parse_args()

    remote_endpoints: list[tuple[str, int]] = []
    for addr in args.remote_peers:
        splitted = addr.split(":")
        if len(splitted) != 2:
            raise ValueError(f"Invalid address: {addr}")
        host, port = splitted
        remote_endpoints.append((host, int(port)))

    run(args.port, remote_endpoints)