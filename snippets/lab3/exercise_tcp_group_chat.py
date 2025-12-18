from snippets.lab3 import *
import sys

"""
How to execute:
poetry run python snippets/lab3/exercise_tcp_group_chat.py port [HOST] [HOST2] [...]
example:
first host: 
first host: poetry run python snippets/lab3/exercise_tcp_group_chat.py 8080
second host: poetry run python snippets/lab3/exercise_tcp_group_chat.py 8081 127.0.0.1:8080
third host: poetry run python snippets/lab3/exercise_tcp_group_chat.py 8082 127.0.0.1:8080
"""

connections: set[Client] = set()
username: str | None = None

def broadcast(msg: str, sender: str, origin=None):
    for peer in list(connections):
        if peer is origin:
            continue
        try:
            peer.send(message(msg, sender))
        except Exception:
            connections.discard(peer)


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Peer {connection.remote_address} disconnected")
            connections.discard(connection)
        case 'error':
            print(error)
            connections.discard(connection)

def on_new_connection(event, connection, address, error):
    match event:
        case 'listen':
            print(f"Listening on port {address[0]} at {', '.join(local_ips())}")
        case 'connect':
            print(f"New connection from {address}")
            connection.callback = on_message_received
            connections.add(connection)
        case 'error':
            print(error)

def main():
    global username

    local_port = int(sys.argv[1])
    initial_peers = sys.argv[2:]

    server = Server(local_port, on_new_connection)

    for peer_endpoint in initial_peers:
        try:
            client = Client(address(peer_endpoint), on_message_received)
            connections.add(client)
            print(f"Connected to peer {client.remote_address}")
        except Exception as e:
            print(f"Failed to connect to {peer_endpoint}: {e}")

    username = input("Enter your username to start the chat:\n")
    print("Type your message and press Enter to send it.")

    try:
        while True:
            content = input()
            if content.strip():
                broadcast(content, username)
    except (EOFError, KeyboardInterrupt):
        print("\nLeaving chat...")
    finally:
        for peer in list(connections):
            peer.close()
        server.close()


if __name__ == "__main__":
    main()
