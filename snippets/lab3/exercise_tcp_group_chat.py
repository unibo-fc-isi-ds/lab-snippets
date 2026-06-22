from snippets.lab3 import *
import sys

"""
How to execute:
poetry run python snippets/lab3/exercise_tcp_group_chat.py port [HOST] [HOST2] [...]
example:
first host: poetry run python snippets/lab3/exercise_tcp_group_chat.py 8080
second host: poetry run python snippets/lab3/exercise_tcp_group_chat.py 8081 127.0.0.1:8080
third host: poetry run python snippets/lab3/exercise_tcp_group_chat.py 8082 127.0.0.1:8080 127.0.0.1:8081

exercise description:
keep all connections in a connections set, once the script start it try to connect to all the passed 
hosts.
Then it ask for a username to use in the chat and keep it in a global variable.
Now it begin a while true loop where a user is asked to insert a message and, if the message is not an
empty message it broadcast it to all other users.
Once the application handle a program interruption exception it send an exit message and it close all the
active connection and the server listener.
methods:
- broadcast: is used to broadcast a message, given the message to send and the sender username
it send the message to all the Clients in the connections list, if a send fails, it remove the hots 
from the connections list
- on_message_received: this is the message receiver callback, once a message is received it check for the
event type and if is a message it print it in the chat else if it is a 'close' or a 'error' event
id discard the client from the connections set.
- on_new_connection: this is the callback called once a new host try to connect to the active server.
once a new connection arrives it set as connection callback the 'on message received' function and it add
the client to the connections list
"""

connections: set[Client] = set()
username: str | None = None

EXIT_MESSAGE = "<LEAVES THE CHAT>"

def broadcast(msg: str, sender: str):
    for peer in list(connections):
        try:
            peer.send(message(msg, sender))
        except Exception:
            connections.discard(peer)


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
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
        case 'stop':
                print(f"Stop listening for new connections")
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
    print("Type your message and press Enter to send it. Messages from other peers will be displayed below.")

    try:
        while True:
            content = input()
            if content.strip():
                broadcast(content, username)
    except (EOFError, KeyboardInterrupt):
        print("\nLeaving chat")
        broadcast(EXIT_MESSAGE, username)
    finally:
        for peer in list(connections):
            peer.close()
        server.close()


if __name__ == "__main__":
    main()
