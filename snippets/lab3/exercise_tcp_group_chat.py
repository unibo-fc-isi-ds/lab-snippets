from snippets.lab3 import *
import sys


def run_chat():
    mode = sys.argv[1].lower()
    global_peer = None

    if mode == "server":
        port = int(sys.argv[2])
        global_peer = Peer("server", port=port, callback=on_message_received)
        print(f"Chat server started on port {port}.")
    elif mode == "client":
        server_address = sys.argv[2]
        global_peer = Peer("client", address=server_address, callback=on_message_received)
        print(f"Connected to chat at {server_address}.")
    else:
        print("Invalid mode. Use 'server' or 'client'.")
        return

    username = input("Enter your username: ").strip()
    print("Type your messages below. Press Ctrl+C to exit.\n"+
          "_______________________________________________")
    try:
        while True:
            content = input()
            if content:
                global_peer.send_chat_message(f"{username}: {content.strip()}")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting chat.")


def on_message_received(event, payload):
    if event == "message":
        print(payload)


if __name__ == "__main__":
    run_chat()
