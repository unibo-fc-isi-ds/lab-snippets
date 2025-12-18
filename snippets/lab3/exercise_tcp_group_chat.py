import sys
from typing import List, Tuple

from snippets.lab3 import Client, Server, address, local_ips, message

remote_peers: List[Client] = []

if len(sys.argv) < 2:
    print(
        "Usage: poetry run python -m snippets.lab3.exercise_tcp_group_chat <PORT> [<PEER1_ADDRESS:PORT> <PEER2_ADDRESS:PORT> ...]"
    )
    sys.exit(1)

try:
    port = int(sys.argv[1])
except ValueError:
    print("Port must be an integer")
    sys.exit(1)

other_peers_addrs: List[Tuple] = []
for addr in sys.argv[2:]:
    other_peers_addrs.append(address(addr))


def send_message(msg: str, sender_username: str):
    if len(remote_peers) == 0:
        print("No peers connected, message is lost")
    elif msg:
        for remote_peer in remote_peers:
            try:
                remote_peer.send(message(msg.strip(), sender_username))
            except Exception as e:
                print(f"Error sending a message to {remote_peer.remote_address}")
                print(f"Cause:\n\t{e}")
    else:
        print("Empty message, not sent")


def on_message_received(event: str, payload: str, connection: Client, error: str):
    match event:
        case "message":
            print(payload)
        case "close":
            print(f"Connection with peer {connection.remote_address} closed")
            try:
                remote_peers.remove(connection)
            except ValueError:
                print(
                    "Unable to remove closed connection from the list of remote peers"
                )
        case "error":
            print(error)


def on_new_connection(event: str, connection: Client, address: List, error: str):
    match event:
        case "listen":
            print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
        case "connect":
            print(f"Open ingoing connection from: {address}")
            connection.callback = on_message_received
            remote_peers.append(connection)
        case "stop":
            print(f"Stop listening for new connections")
        case "error":
            print(error)


username = input("Enter your username to start the chat:\n")

server = Server(port, on_new_connection)

for addr in other_peers_addrs:
    try:
        remote_peers.append(Client(addr, on_message_received))
        print(f"Connected to client at {addr[0]}:{addr[1]}")
    except Exception as e:
        print(f"Couldn't connect to {addr[0]}:{addr[1]}")
        print(f"Cause:\n\t{e}")


print(
    "Type your message and press Enter to send it. Messages from other peers will be displayed below."
)

while True:
    try:
        content = input()
        send_message(content, username)
    except (EOFError, KeyboardInterrupt):
        for remote_peer in remote_peers:
            remote_peer.close()
        break

server.close()
