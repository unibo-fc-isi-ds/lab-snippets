import sys
from datetime import datetime
from snippets.lab2 import address
from snippets.lab3 import Client, Server, message
from snippets.lab3 import *

class GroupPeer:
    def __init__(self, port: int, peers=None):
        self.peers = []
        self.local_addr = ("", port)
        self.server = Server(port, self.on_server_event)

        if peers:
            targets = list({peer for peer in peers})
            for peer in targets:
                try:
                    conn = Client(peer, self.on_connection_event)
                    self.peers.append(conn)
                except:
                    pass

    def broadcast(self, msg, sender):
        if not msg or not self.peers:
            print(f"{RED_CLR}\nNo peer connected, message is lost{RESET_CLR}\n")
            return

        packet = message(msg.strip(), sender) + MSG_ENCODE

        for peer in list(self.peers):
            try:
                peer.send(packet)
            except:
                self._remove_peer(peer)

    def exit(self, sender):
        now = datetime.now().isoformat()

        exit_packet = f"\n[{now}]{EXIT_SEPARATOR}\n{PURPLE_CLR}{sender} {EXIT_MESSAGE} {RESET_CLR} {EXIT_ENCODE}"

        for peer in list(self.peers):
            try:
                peer.send(exit_packet)
            except:
                pass

        self._close_all()

    def _remove_peer(self, peer):
        try:
            if peer in self.peers:
                self.peers.remove(peer)
        except:
            pass

        try:
            peer.close()
        except:
            pass

    def on_connection_event(self, event, payload, connection, error):
        if event == "message":
            cleaned = (
                payload.replace(MSG_ENCODE, "")
                       .replace(EXIT_ENCODE, "")
                       .rstrip()
            )
            if cleaned:
                print(cleaned)
        elif event in ["close", "error"]:
            self._remove_peer(connection)

    def on_server_event(self, event, connection, address, error):
        if event == "listen":
            self.local_addr = address

        elif event == "connect":
            connection.callback = self.on_connection_event
            self.peers.append(connection)

    def _close_all(self):
        for peer in list(self.peers):
            try:
                peer.close()
            except:
                pass

        try:
            self.server.close()
        except:
            pass

username = input(f"{PURPLE_CLR}Enter your username to start the chat:{RESET_CLR}\n")
port = int(sys.argv[1])

if len(sys.argv) > 2:
    peers = [address(p) for p in sys.argv[2:]]
    node = GroupPeer(port, peers)
else:
    node = GroupPeer(port)

print(f"{CYAN_CLR}\n{READY_MESSAGE}{RESET_CLR}\n")

try:
    while True:
        text = input()

        if text.strip() == "/exit":
            raise KeyboardInterrupt
        if not text:
            continue
        print(f"{PREV_LINE}{YELLOW_CLR}{text}{RESET_CLR}{CLEAR_RIGHT}")
        node.broadcast(text, username)

except (KeyboardInterrupt, EOFError):
    node.exit(username)
    print(f"{PURPLE_CLR}Bye!{RESET_CLR}")
    sys.exit(0)
