from snippets.lab3 import *
import sys


mode = sys.argv[1].lower().strip()

def get_msg_str(msg, sender) -> str:
    return message(msg.strip(), sender)

def run_client(remote_endpoint: str): 
    remote_peer: Client | None = None
    def on_message_received(event, payload, connection, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                print(f"Connection with peer {connection.remote_address} closed")
                nonlocal remote_peer
                remote_peer = None
            case 'error':
                print(error)
    
    username = input('Enter your username to start the chat:\n')
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

    remote_peer = Client(address(remote_endpoint), on_message_received)
    print(f"Connected to {remote_peer.remote_address}")

    while True:
        try:
            content = input()
            if remote_peer is None:
                print("Error: Disconnected from server")
                break
            if not content:
                continue  # Empty message, skip
            remote_peer.send(get_msg_str(content, username))
        except (EOFError, KeyboardInterrupt):
            if remote_peer is not None:
                remote_peer.close()
            break

def run_server(port: int):
    server_connections: dict[str, Connection] = {}

    def on_message_server(event, payload, connection, error):
        match event:
            case 'message':
                for conn in server_connections.values():
                    if conn.remote_address == connection.remote_address:
                        continue  # Do not echo back to sender
                    conn.send(payload)
            case 'close':
                print(f"Connection with peer {connection.remote_address} closed")
                del server_connections[connection.remote_address]  # Remove peer
            case 'error':
                print(error)

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
    try:
        server.join()
    except KeyboardInterrupt:
        server.close()

if __name__ == "__main__":
    mode = sys.argv[1].lower().strip()
    match mode:
        case "server":
            run_server(port=int(sys.argv[2]))
        case "client":
            run_client(remote_endpoint=sys.argv[2])
        case _:
            raise ValueError(f"Invalid mode: {mode}")