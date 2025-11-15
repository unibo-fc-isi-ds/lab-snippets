from snippets.lab3 import *
from peer_state import PeerState
from message_lib import make_message
import threading
import json
import sys


def user_input_loop(state):
	while True:
		try:
			text = input()
		except (EOFError, KeyboardInterrupt):
			for p in list(state.peers):
				p.close()
			break

		if not text.strip():
			continue

		msg_json = make_message(text.strip(), state.username)
		msg_id = json.loads(msg_json)["id"]
		state.remember(msg_id)

		state.broadcast(msg_json)


def main():
	if len(sys.argv) < 2:
		print("Uso: python exercise_tcp_group_chat.py <port> [peer1 peer2 ...]")
		return

	listen_port = int(sys.argv[1])
	initial_peers = sys.argv[2:]
	username = input("Inserisci username:\n")

	# creo lo state del peer
	state = PeerState(username, listen_port, initial_peers)

	# server locale
	state.server = Server(listen_port, state.on_new_connection)

	# connessione ai peer iniziali
	state.connect_to_initial_peers()

	print("Chat pronta.")

	# thread input
	t = threading.Thread(target=user_input_loop, args=(state,), daemon=True)
	t.start()
	t.join()

	state.server.close()


if __name__ == "__main__":
	main()
