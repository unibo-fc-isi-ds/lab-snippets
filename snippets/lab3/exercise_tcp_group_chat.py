from snippets.lab3 import *
import sys
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description="TCP group-chat exercise")
    parser.add_argument("--mode", help="Mode to run the chat in", choices=["standard", "bootstrap"])
    parser.add_argument("--b_port", help="Port to bind for bootstrap socket", type=int)
    parser.add_argument("--w_port", help="Port to bind for welcoming socket", type=int)
    parser.add_argument("--remote_endpoint", help="Remote endpoint to connect to", type=str)


    args = parser.parse_args()


    #callback used to manage bootstrap protocol
    def on_new_bootstrap_connection(event, address, error, peers_list):
        match event:
            case 'listen':
                print(f"Bootstraping socket listening on port {address[1]} at {', '.join(local_ips())}")
            case 'connect_ingoing':
                print(f"Open temporary ingoing connection for peer retrieval from user on: {address}")
            case 'send_peers':
                print(f"Sending peers: {peers_list} to user on: {address}")
            case 'stop':
                print(f"Stop listening for new peer retrieval connections")
            case 'close':
                print(f"Close temporary connection for peer retrieval from user on: {address}")
            case 'error':
                print(error)

            

    def on_new_connection(event, connection: Connection, connections: list[Connection], address, error):
        match event:
            case 'listen':
                print(f"Welcoming socket listening on port {address[1]} at {', '.join(local_ips())}")
            case 'connect_ingoing':
                print(f"Open ingoing connection from user [{connection.id}] on: {address}")
                connection.callback = partial(on_message_received, connections = connections)
            case 'connect_outgoing':
                print(f"Open outgoing connection to user [{connection.id}] on: {address}")
                connection.callback = partial(on_message_received, connections = connections)
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)


    def on_message_received(event, payload, connection, error, connections):
        match event:
            case 'message':
                print(payload)
            case 'close':
                print(f"Connection with peer user [{connection.id}] over {connection.remote_address} closed")
                connections.remove(connection)
            case 'error':
                print(error)


    if args.mode == 'standard':
        port = args.w_port
        starting_endpoint = args.remote_endpoint

        

    if args.mode == 'bootstrap':
        bootstrap_port = args.b_port
        port = args.w_port
        starting_endpoint = args.remote_endpoint




    username = input('Enter your username to start the chat:\n')
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')

    try:
        if args.mode == 'standard':
            peer = Peer(username, int(port), starting_endpoint, on_new_connection)
        if args.mode == 'bootstrap':
            peer = Peer(username, int(port), starting_endpoint, callback = on_new_connection, is_bootstraping=True, bootstrap_port=bootstrap_port, bootstrap_callback=on_new_bootstrap_connection)

        peer.init_connect(peers_connection_callback = on_message_received)

        print("Connection established. You can start chatting now.")

        while True:
            content = input()
            peer.send_all(content)

    except (EOFError, KeyboardInterrupt):
        peer.close()
    
    print("Connection closed. Exiting program.")
    




if __name__ == "__main__":
    main()