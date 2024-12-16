import sys
from snippets.lab3 import *

class Peer:
    def __init__(self, port, initial_peers=None):
        self.server = Server(port, self.new_connection)
        self.clients = set()

        if initial_peers:
            for peer in initial_peers:
                self.connect(peer)

    def new_connection(self, event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"New incoming connection from {address}")
                connection.callback = self.message_received
                self.clients.add(connection)
            case 'stop':
                print("Stopped listening for new connections.")
            case 'error':
                print(f"Error occurred: {error}")

    def connect(self, endpoint):
        try:
            remote_peer = Client(address(endpoint), self.message_received)
            self.clients.add(remote_peer)
        except Exception as e:
            print(f"Failed to connect to {endpoint}: {e}")
            sys.exit(1)

    def broadcast(self, message_content, user):
        if self.clients:
            for client in set(self.clients):
                try:
                    client.send(message(message_content.strip(), user))
                except Exception as e:
                    print(f"Error: {e}")
                    self.clients.remove(client)

    def message_received(self, event, payload, connection, error):
        match event:
            case 'message':
                print(payload)
            case 'close':
                print(f"Connection with {connection.remote_address} closed.")
                self.clients.discard(connection)
            case 'error':
                print(f"Error: {error}")
                if connection in self.clients:
                    self.clients.remove(connection)

    def start_chat(self):
        print("Enter your username to start.")
        username = input()
        print("Type a message and press Enter to send it.")

        try:
            while True:
                content = input()
                if content.strip() == "/exit":
                    self.broadcast("\nDisconnecting\n", username)
                    print("Disconnected.")
                    break
                self.broadcast(content, username)
        except (EOFError, KeyboardInterrupt):
            self.broadcast("\nDisconnecting\n", username)
            for client in set(self.clients):
                client.close()
            print("Disconnected")
            self.server.close()
        finally:
            for client in set(self.clients):
                client.close()
            self.server.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a port number.")
        sys.exit(1)

    port = int(sys.argv[1])
    peers = sys.argv[2:] if len(sys.argv) > 2 else None

    chat_peer = Peer(port, peers)

    try:
        chat_peer.start_chat()
    except KeyboardInterrupt:
        print("\nChat interrupted. Shutting down...")
        chat_peer.server.close()
