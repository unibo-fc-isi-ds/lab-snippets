import sys
import time
import threading
import queue
from snippets.lab3 import *

if len(sys.argv) < 3:
    print("Too few arguments have been passed")
    exit(1)

listen_port = int(sys.argv[1])

peers = []
for p in sys.argv[2:]:
    ip, port = p.split(":")
    peers.append((ip, int(port)))

username = input("Insert username:\n")

peer = Peer(username, listen_port, peers)

print("Chat initialized. Type a message and hit Enter")

msg_queue = queue.Queue()
running = True

def input_thread():
    """Reads user input without blocking main thread."""
    while running:
        try:
            msg = input()
            msg_queue.put(msg)
        except EOFError:
            break

t = threading.Thread(target=input_thread, daemon=True)
t.start()

try:
    while True:
        try:
            msg = msg_queue.get(timeout=0.1)
            if msg.strip():
                peer.broadcast(f"Message from {username}:\n\t{msg}")
        except queue.Empty:
            pass
except KeyboardInterrupt:
    print("\nExiting the chat...")
finally:
    running = False
    peer.close()
    time.sleep(0.1)
    sys.exit(0)
