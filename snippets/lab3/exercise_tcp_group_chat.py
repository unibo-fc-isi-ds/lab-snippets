from snippets.lab3 import *
import sys
import time

mode = sys.argv[1].lower().strip()
peers: list[Client] = []
remote_peer: Client | None = None
running = True


def broadcast_message(msg: str, sender: str, exclude: Client | None = None):
    if not msg.strip() or not running:
        return
    for peer in peers[:]:
        if peer is exclude:
            continue
        try:
            peer.send(message(msg.strip(), sender))
        except Exception as e:
            if running:
                print(f"Failed to send to {peer.remote_address}: {e}")
            peers.remove(peer)


def on_message_received(event, payload, connection, error):
    global running
    if not running:
        return

    match event:
        case 'message':
            print(f"[{connection.remote_address}] {payload}")
            if connection not in peers:
                peers.append(connection)
            broadcast_message(payload, sender=str(
                connection.remote_address), exclude=connection)

        case 'connect':
            if connection not in peers:
                peers.append(connection)
            print(f"Connected to new peer: {connection.remote_address}")

        case 'close':
            if connection in peers:
                peers.remove(connection)
            print(f"Peer disconnected: {connection.remote_address}")

        case 'error':
            ignore_error = False
            if not running:
                ignore_error = True
            elif hasattr(error, 'winerror') and error.winerror == 10054:
                ignore_error = True
            if not ignore_error:
                print(f"Error with {connection.remote_address}: {error}")
            if connection in peers:
                peers.remove(connection)


def connect_to_peer(endpoint: str):
    try:
        peer = Client(address(endpoint), on_message_received)
        if peer not in peers:
            peers.append(peer)
        print(f"Connected to peer {peer.remote_address}")
    except Exception as e:
        print(f"Failed to connect to {endpoint}: {e}")


if mode == 'client':
    if len(sys.argv) < 3:
        print("Usage: python chat.py client <peer_address>")
        sys.exit(1)

    connect_to_peer(sys.argv[2])

    try:
        username = input("Enter your username: ")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        sys.exit(0)

    print("Type messages below. Ctrl+C to exit.")
    try:
        while running:
            msg = input()
            broadcast_message(msg, username)
    except (EOFError, KeyboardInterrupt):
        print("\nExiting chat...")
        running = False

elif mode == 'server':
    if len(sys.argv) < 3:
        print("Usage: python chat.py server <port>")
        sys.exit(1)

    port = int(sys.argv[2])

    def on_new_connection(event, connection, address, error):
        if not running:
            return
        match event:
            case 'listen':
                print(
                    f"Server listening on {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"New peer connected: {address}")
                connection.callback = on_message_received
                if connection not in peers:
                    peers.append(connection)
            case 'stop':
                print("Stopped listening")
            case 'error':
                print(f"Server error: {error}")

    server = Server(port, on_new_connection)
    print("Server running. Press Ctrl+C to stop.")

    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nServer stopping...")
        running = False

# Close all peers gracefully
for peer in peers:
    try:
        peer.close()
    except:
        pass

if mode == 'server':
    try:
        server.close()
    except:
        pass
