import sys
import queue
from node.node import Node
from ui.ui_tk import TkChatUI


def main():
	if len(sys.argv) < 3:
		print("Correct usage:")
		print("   python exercise_tcp_group_chat.py <name> <port> [host:port ...]")
		print("Example:")
		print("   python exercise_tcp_group_chat.py Alice 8000 127.0.0.1:8200 192.168.1.5:9001")
		return

	name = sys.argv[1]

	# validate local port
	try:
		port = int(sys.argv[2])
		if not (0 < port < 65536):
			raise ValueError
	except ValueError:
		print(f"Error: port must be an integer between 1 and 65535, got '{sys.argv[2]}'")
		return

	# parse initial peers
	peers = []
	for entry in sys.argv[3:]:
		if ":" not in entry:
			print(f"Invalid peer '{entry}': expected format host:port")
			print("Example: 127.0.0.1:8200")
			return

		host, port_str = entry.split(":", 1)

		try:
			peer_port = int(port_str)
			if not (0 < peer_port < 65536):
				raise ValueError
		except ValueError:
			print(f"Invalid peer '{entry}': port must be an integer between 1 and 65535")
			return

		peers.append((host, peer_port))

	# UI queue
	ui_queue = queue.Queue()

	# start node
	try:
		node = Node(name=name, port=port, peers=peers, queue_ui=ui_queue)
	except Exception as e:
		print("Error while starting the node:", e)
		return

	# start UI
	ui = TkChatUI(node)
	ui.start()


if __name__ == "__main__":
	main()
